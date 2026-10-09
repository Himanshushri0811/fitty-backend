import logging
import os
import re
import uuid
from datetime import datetime, timedelta

import mongoengine
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from mongoengine.queryset.visitor import Q
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import generate_jwt
from .models import User, GymOwner, WorkoutDay, WorkoutExercise, WorkoutFeedback
from .workout_plans import DEFAULT_WORKOUT_PLANS

# import razorpay -> VerifyPaymentAPIView ke andar import hota hai (startup crash se bachne ke liye)

logger = logging.getLogger(__name__)


# ============================================================================
# HELPERS
# ============================================================================
def _as_date(value):
    """DailyCalorieLog.date kabhi date aur kabhi datetime aa sakta hai. Dono handle."""
    if value is None:
        return None
    return value.date() if isinstance(value, datetime) else value


def abs_media(request, url):
    """Relative /media/... URL ko full https://backend/media/... bana deta hai."""
    if not url:
        return ''
    if url.startswith(('http://', 'https://')):
        return url
    return request.build_absolute_uri(url)


def get_auth_user(request):
    """Logged-in user ya None (AnonymousUser / None dono handle)."""
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'id', None):
        return None
    # Nakli/demo user (jo DB document nahi hai) ko reject karo, warna .save() pe 500 aata hai
    if not callable(getattr(user, 'save', None)):
        return None
    return user


def build_user_payload(user, request):
    """Login, Signup aur Profile teeno me yahi shape jata hai -> frontend me mismatch nahi."""
    return {
        'id': str(user.id),
        'email': user.email,
        'role': user.role,
        'name': user.name if user.name else getattr(user, 'gym_name', None) or user.username,
        'username': user.username,
        'bio': getattr(user, 'bio', '') or '',
        'profile_pic': abs_media(request, getattr(user, 'profile_pic', '') or ''),
        'cover_pic': abs_media(request, getattr(user, 'cover_pic', '') or ''),
        'gym_name': getattr(user, 'gym_name', None),
        'plan': getattr(user, 'plan_type', 'FREE'),
    }


def compute_streak(user, today=None):
    """Consecutive days (aaj ya kal tak) jisme calories_burned > 0."""
    today = today or datetime.utcnow().date()
    active = set()
    for log in (getattr(user, 'daily_calories_log', None) or []):
        d = _as_date(log.date)
        if d and (log.calories_burned or 0) > 0:
            active.add(d)
    cursor = today if today in active else today - timedelta(days=1)
    streak = 0
    while cursor in active:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _to_float(val):
    if val in (None, ''):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        raise ValueError('Numeric value expected')


# ============================================================================
# PASSWORD RESET
# ============================================================================
class ForgotPasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()

        if not email:
            return Response({'error': 'Email is required'}, status=400)

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return Response({'error': 'Invalid email format'}, status=400)

        user = User.objects(email=email).first()

        # Hamesha 200 return karo taaki koi email enumerate na kar sake
        if not user:
            logger.info(f"Forgot password requested for non-existent email: {email}")
            return Response({'message': 'If an account exists with this email, a reset link has been sent.'}, status=200)

        token = str(uuid.uuid4())
        expiry_time = datetime.utcnow() + timedelta(minutes=20)

        user.reset_password_token = token
        user.reset_password_expiry = expiry_time
        user.save()

        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://fitty-ai.netlify.app')
        reset_link = f"{frontend_url}/auth/reset-password/{token}"

        subject = "Reset Your FitMitra Password"
        message = f"""
Click the link below to reset your password:

{reset_link}

This link will expire in 20 minutes.

If you did not request this, please ignore this email.
"""

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            logger.info(f"Reset email sent to {email}")
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return Response({'error': 'Failed to send email. Please try again later.'}, status=500)

        return Response({'message': 'If an account exists with this email, a reset link has been sent.'})


class VerifyResetTokenAPIView(APIView):
    def get(self, request):
        token = request.query_params.get('token')

        if not token:
            return Response({'error': 'Token is required'}, status=400)

        user = User.objects(reset_password_token=token).first()

        if not user:
            return Response({'valid': False, 'error': 'Invalid or expired token'}, status=400)

        if user.reset_password_expiry < datetime.utcnow():
            return Response({'valid': False, 'error': 'Token has expired'}, status=400)

        return Response({'valid': True, 'message': 'Token is valid'})


class ResetPasswordAPIView(APIView):
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token or not new_password:
            return Response({'error': 'Token and new password are required'}, status=400)

        if len(new_password) < 6:
            return Response({'error': 'Password must be at least 6 characters'}, status=400)

        user = User.objects(reset_password_token=token).first()

        if not user:
            return Response({'error': 'Invalid or used token'}, status=400)

        if user.reset_password_expiry < datetime.utcnow():
            return Response({'error': 'Token has expired'}, status=400)

        user.set_password(new_password)
        user.reset_password_token = None
        user.reset_password_expiry = None
        user.save()

        return Response({'message': 'Password reset successfully'})


# ============================================================================
# HEALTH CHECK
# ============================================================================
@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        db_status = "Connected"
        try:
            from mongoengine.connection import get_db
            get_db().command("ping")
        except Exception:
            db_status = "Disconnected"

        return Response({
            "status": "ok",
            "database": db_status,
            "version": "1.1.0-unbreakable",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })


# ============================================================================
# SIGNUP
# ============================================================================
@method_decorator(csrf_exempt, name='dispatch')
class SignupAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            data = request.data
            email = data.get('email', '').strip().lower()
            password = data.get('password')
            name = data.get('name', '').strip()

            role = data.get('role', 'USER')

            # Security: API se Admin account nahiban sakta
            if role == 'ADMIN':
                return Response({'error': 'Admin accounts cannot be created via Signup API.'}, status=403)

            if not role or role not in ['USER', 'GYM_OWNER']:
                if 'gym_name' in data or 'gym-owner' in request.path:
                    role = 'GYM_OWNER'
                else:
                    role = 'USER'

            if not email or not password:
                return Response({'error': 'Email and password required'}, status=400)

            # Username: lowercase me store karte hain taaki ambiguity na ho
            username = data.get('username')
            if username:
                username = username.strip().lower()
            else:
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                while User.objects(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1

            existing_user = User.objects(Q(email=email) | Q(username=username)).first()
            if existing_user:
                return Response({'error': 'Email or Username already taken'}, status=400)

            user = User(
                email=email,
                username=username,
                role=role,
                name=name
            )

            if role == 'GYM_OWNER':
                user.gym_name = data.get('gym_name', 'My Gym')
                user.gym_address = data.get('gym_address', '')
            else:
                user.goal = data.get('goal', '')

                try:
                    age_val = data.get('age')
                    if age_val is not None and str(age_val).strip():
                        user.age = int(float(age_val))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid age provided: {data.get('age')}")

                user.gender = data.get('gender', '')
                user.mobile = data.get('mobile', '')
                user.dob = data.get('dob')

                # Frontend terminology -> backend choices
                raw_activity = data.get('activity_level', 'Beginner')
                activity_map = {
                    'Beginner': 'Moderately Active',
                    'Intermediate': 'Very Active',
                    'Advanced': 'Super Active'
                }
                user.activity_level = activity_map.get(raw_activity, raw_activity)

                user.fitness_level = data.get('fitness_level', 'Beginner')

                try:
                    height_val = data.get('height')
                    if height_val is not None and str(height_val).strip():
                        user.height = float(height_val)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid height provided: {data.get('height')}")

                try:
                    weight_val = data.get('weight')
                    if weight_val is not None and str(weight_val).strip():
                        user.weight = float(weight_val)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid weight provided: {data.get('weight')}")

            user.set_password(password)
            user.save()

            tokens = generate_jwt(user)

            return Response({
                'user': build_user_payload(user, request),
                'access': tokens['access'],
                'refresh': tokens['refresh']
            }, status=201)
        except mongoengine.errors.ValidationError as ve:
            return Response({
                'error': 'Validation Error',
                'details': str(ve)
            }, status=400)
        except Exception as e:
            logger.error("Signup Error Traceback: ", exc_info=True)
            return Response({
                'error': 'Internal Server Error. Check server logs.',
                'details': str(e),
                'type': type(e).__name__
            }, status=500)


# ============================================================================
# LOGIN  (hardcoded admin/test failsafe hata diya: wo security hole tha)
# ============================================================================
@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = str(request.data.get('email') or request.data.get('username') or '').strip().lower()
        password = str(request.data.get('password') or '')

        if not identifier or not password:
            return Response({'error': 'Email/username and password are required'}, status=400)

        try:
            user = User.objects(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
        except Exception:
            logger.error('Database error during login', exc_info=True)
            return Response({'error': 'Database unavailable. Try again shortly.'}, status=503)

        if not user or not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=401)

        tokens = generate_jwt(user)
        return Response({
            'user': build_user_payload(user, request),
            'access': tokens['access'],
            'refresh': tokens['refresh'],
        })


# ============================================================================
# PROFILE
# ============================================================================
class ProfileView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = get_auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)

        bmi, bmi_category, ideal_weight_range = None, 'N/A', 'N/A'
        if user.height and user.weight:
            h_m = user.height / 100
            bmi = round(user.weight / (h_m * h_m), 1)
            if bmi < 18.5:
                bmi_category = 'Underweight'
            elif bmi < 25:
                bmi_category = 'Normal'
            elif bmi < 30:
                bmi_category = 'Overweight'
            else:
                bmi_category = 'Obese'
            ideal_weight_range = f"{round(18.5 * h_m * h_m, 1)} - {round(24.9 * h_m * h_m, 1)} kg"

        data = build_user_payload(user, request)
        data.update({
            'age': getattr(user, 'age', None),
            'gender': getattr(user, 'gender', ''),
            'height': getattr(user, 'height', None),
            'weight': getattr(user, 'weight', None),
            'goal': getattr(user, 'goal', ''),
            'fitness_level': getattr(user, 'fitness_level', 'Beginner'),
            'target_weight': getattr(user, 'target_weight', None),
            'activity_level': getattr(user, 'activity_level', 'Moderately Active'),
            'diet_preference': getattr(user, 'diet_preference', 'Non-Vegetarian'),
            'medical_conditions': list(getattr(user, 'medical_conditions', []) or []),
            'allergies': list(getattr(user, 'allergies', []) or []),
            'preferred_workout_type': getattr(user, 'preferred_workout_type', 'Gym'),
            'mobile': getattr(user, 'mobile', ''),
            'dob': str(getattr(user, 'dob', '') or ''),
            'gym_address': getattr(user, 'gym_address', ''),
            'bmi': bmi,
            'bmi_category': bmi_category,
            'ideal_weight_range': ideal_weight_range,
            'workouts_completed': getattr(user, 'workouts_completed', 0),
            'streak': compute_streak(user),
            'followers_count': len(getattr(user, 'followers', None) or []),
            'following_count': len(getattr(user, 'following', None) or []),
            'calories_burned': round(sum(
                (l.calories_burned or 0) for l in (getattr(user, 'daily_calories_log', None) or [])
            )),
        })
        return Response(data)

    def put(self, request):
        user = get_auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)

        data = request.data

        if 'name' in data:
            name = str(data['name']).strip()
            if not name:
                return Response({'error': 'Name cannot be empty'}, status=400)
            if len(name) > 50:
                return Response({'error': 'Name must be 50 characters or fewer'}, status=400)
            user.name = name

        if 'bio' in data:
            bio = str(data['bio']).strip()
            if len(bio) > 200:
                return Response({'error': 'Bio must be 200 characters or fewer'}, status=400)
            user.bio = bio

        for field in ['age', 'height', 'weight', 'target_weight']:
            if field in data:
                try:
                    val = _to_float(data[field])
                except ValueError:
                    return Response({'error': f'{field} must be a number'}, status=400)
                if field == 'age' and val is not None:
                    val = int(val)
                setattr(user, field, val)

        for field in ['gender', 'goal', 'fitness_level', 'gym_address', 'gym_name', 'mobile',
                      'dob', 'activity_level', 'diet_preference', 'preferred_workout_type']:
            if field in data:
                setattr(user, field, data[field])

        for field in ['medical_conditions', 'allergies']:
            if field in data and isinstance(data[field], list):
                setattr(user, field, data[field])

        # Weight history: sirf tab jab weight sach me badla ho
        if 'weight' in data and user.weight:
            try:
                from .models import WeightLog
                last = user.weight_history[-1].weight if user.weight_history else None
                if last != user.weight:
                    user.weight_history.append(WeightLog(weight=user.weight, date=datetime.utcnow()))
            except Exception:
                logger.warning('weight history update failed', exc_info=True)

        try:
            user.save()
        except mongoengine.errors.ValidationError as ve:
            logger.warning('Profile validation failed', exc_info=True)
            return Response({'error': 'Some profile data is invalid', 'details': str(ve)}, status=400)
        except Exception as e:
            logger.error('Profile save failed', exc_info=True)
            return Response({'error': 'Could not save profile', 'details': str(e)}, status=500)
        return self.get(request)


# ============================================================================
# PROFILE / COVER IMAGE UPLOAD
# ============================================================================
ALLOWED_IMG = {'jpg', 'jpeg', 'png', 'webp'}
MAX_IMG_BYTES = 5 * 1024 * 1024


class UploadProfilePicView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = get_auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)

        is_cover = 'cover_pic' in request.FILES
        file_obj = request.FILES.get('cover_pic') if is_cover else request.FILES.get('profile_pic')
        if not file_obj:
            return Response({'error': 'No file uploaded'}, status=400)

        ext = file_obj.name.rsplit('.', 1)[-1].lower() if '.' in file_obj.name else ''
        if ext not in ALLOWED_IMG or not (file_obj.content_type or '').startswith('image/'):
            return Response({'error': 'Only JPG, PNG or WEBP images are allowed'}, status=400)
        if file_obj.size > MAX_IMG_BYTES:
            return Response({'error': 'Image is too large (max 5 MB)'}, status=400)

        try:
            prefix = 'cover' if is_cover else 'avatar'
            filename = f"users/{user.id}/{prefix}_{int(datetime.now().timestamp())}.{ext}"
            saved_name = default_storage.save(filename, ContentFile(file_obj.read()))
            new_url = default_storage.url(saved_name)  # local ya Cloudinary/S3, dono me sahi

            old_url = (user.cover_pic if is_cover else user.profile_pic) or ''
            if is_cover:
                user.cover_pic = new_url
            else:
                user.profile_pic = new_url
            user.save()

            # Purani local file hatao (best effort)
            try:
                if settings.MEDIA_URL and old_url.startswith(settings.MEDIA_URL):
                    default_storage.delete(old_url[len(settings.MEDIA_URL):])
            except Exception:
                pass

            return Response({
                'status': 'success',
                'profile_pic': abs_media(request, user.profile_pic or ''),
                'cover_pic': abs_media(request, user.cover_pic or ''),
            })
        except Exception:
            logger.error('Profile image upload failed', exc_info=True)
            return Response({'error': 'Upload failed. Please try again.'}, status=500)


# ============================================================================
# PAYMENT
# ============================================================================
class VerifyPaymentAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            user = get_auth_user(request)
            if user and user.role == 'GYM_OWNER':
                user.update_plan('PRO')
                return Response({'status': 'Payment Verified', 'plan': 'PRO'})
            return Response({'error': 'User mismatch'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


# ============================================================================
# WORKOUT PLAN
# ============================================================================
class UserWorkoutPlanAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = get_auth_user(request)
        if not user or user.role != 'USER':
            return Response({'error': 'Unauthorized'}, status=401)

        force_refresh = request.query_params.get('force', 'false') == 'true'

        # 1. Generate / Regenerate Plan
        if force_refresh or not user.weekly_plan:
            goal = user.goal or "Hybrid / All-Round Fitness"
            template = DEFAULT_WORKOUT_PLANS.get(goal)

            if not template:
                for key in DEFAULT_WORKOUT_PLANS.keys():
                    if key.lower() in goal.lower() or goal.lower() in key.lower():
                        template = DEFAULT_WORKOUT_PLANS[key]
                        break
                if not template:
                    template = DEFAULT_WORKOUT_PLANS["Hybrid / All-Round Fitness"]

            new_plan = []
            for day_data in template:
                day_exercises = []
                for ex_data in day_data['exercises']:
                    day_exercises.append(WorkoutExercise(
                        name=ex_data['name'],
                        sets=ex_data['sets'],
                        reps=ex_data['reps'],
                        description=ex_data.get('description', ''),
                        video_url=ex_data.get('video_url', '')
                    ))
                new_plan.append(WorkoutDay(
                    day_name=day_data['day_name'],
                    focus=day_data['focus'],
                    exercises=day_exercises
                ))

            user.weekly_plan = new_plan
            user.save()

        # 2. Adaptive logic (thakaan ho to sets kam karo)
        response_plan = []
        recent_feedbacks = user.workout_history[-3:] if user.workout_history else []
        high_fatigue_count = sum(1 for f in recent_feedbacks if f.fatigue_level >= 8)
        poor_form_count = sum(1 for f in recent_feedbacks if f.form_quality == 'Poor')
        scale_down = high_fatigue_count > 0 or poor_form_count > 0

        for day in user.weekly_plan:
            day_dict = {
                'day_name': day.day_name,
                'focus': day.focus,
                'exercises': []
            }

            day_is_today = day.day_name.lower() == datetime.now().strftime('%A').lower()

            for ex in day.exercises:
                ex_dict = {
                    'name': ex.name,
                    'sets': ex.sets,
                    'reps': ex.reps,
                    'description': ex.description,
                    'video_url': getattr(ex, 'video_url', '')
                }

                # Custom URL nahi hai to local video dhundo
                if not ex_dict['video_url']:
                    filename = ex.name.replace(" ", "_").replace("/", "_") + ".mp4"
                    local_path = os.path.join(settings.MEDIA_ROOT, 'exercises', filename)
                    if os.path.exists(local_path):
                        relative_url = f"{settings.MEDIA_URL}exercises/{filename}"
                        ex_dict['video_url'] = request.build_absolute_uri(relative_url)

                if scale_down and day_is_today:
                    try:
                        if 'sets' in ex_dict and str(ex_dict['sets']).isdigit():
                            current_sets = int(ex_dict['sets'])
                            if current_sets > 2:
                                ex_dict['sets'] = str(current_sets - 1)
                                ex_dict['adaptive_note'] = "Reduced volume due to recent fatigue."
                    except Exception:
                        pass

                day_dict['exercises'].append(ex_dict)
            response_plan.append(day_dict)

        return Response(response_plan)

    def put(self, request):
        """Kisi ek din ka focus ya exercises edit karo"""
        user = get_auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)

        data = request.data
        day_index = data.get('day_index')

        if not isinstance(day_index, int) or not (0 <= day_index < len(user.weekly_plan or [])):
            return Response({'error': 'Invalid day index'}, status=400)

        day_obj = user.weekly_plan[day_index]

        if 'focus' in data:
            day_obj.focus = data['focus']

        if 'exercises' in data:
            new_ex_list = []
            for ex in data['exercises']:
                new_ex_list.append(WorkoutExercise(
                    name=ex.get('name', 'Exercise'),
                    sets=str(ex.get('sets', '3')),
                    reps=str(ex.get('reps', '10')),
                    description=ex.get('description', ''),
                    video_url=ex.get('video_url', '')
                ))
            day_obj.exercises = new_ex_list

        user.save()
        return Response({'status': 'Plan updated'})


# ============================================================================
# DASHBOARD STATS
# ============================================================================
class DashboardStatsAPI(APIView):
    """
    GET /api/accounts/dashboard/stats/?date=YYYY-MM-DD
    `date` client ka local date hai, taaki IST/UTC ka farq na aaye.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = get_auth_user(request)
        if not user or getattr(user, 'role', None) != 'USER':
            return Response({'error': 'Unauthorized'}, status=401)

        try:
            today = datetime.strptime(request.query_params.get('date', ''), '%Y-%m-%d').date()
        except ValueError:
            today = datetime.utcnow().date()

        burned, consumed = {}, {}
        for log in (user.daily_calories_log or []):
            d = _as_date(log.date)
            if not d:
                continue
            burned[d] = burned.get(d, 0) + (log.calories_burned or 0)
            consumed[d] = consumed.get(d, 0) + (log.calories_consumed or 0)

        monday = today - timedelta(days=today.weekday())
        weekly = []
        for i in range(7):
            d = monday + timedelta(days=i)
            weekly.append({
                'name': d.strftime('%a'),
                'calories': round(burned.get(d, 0)),
                'consumed': round(consumed.get(d, 0)),
            })

        return Response({
            'weekly': weekly,
            'streak': compute_streak(user, today),
            'workouts_completed': getattr(user, 'workouts_completed', 0),
            'target_weight': user.target_weight,
            'current_weight': user.weight,
            'name': user.name or user.username,
            'profile_pic': abs_media(request, getattr(user, 'profile_pic', '') or ''),
        })


# ============================================================================
# WORKOUT FEEDBACK / EXPLANATION
# ============================================================================
class WorkoutFeedbackAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = get_auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)

        data = request.data
        try:
            feedback = WorkoutFeedback(
                workout_day_index=data.get('day_index', 0),
                difficulty=data.get('difficulty', 'Medium'),
                fatigue_level=int(data.get('fatigue', 5)),
                form_quality=data.get('form', 'Good')
            )
            if not user.workout_history:
                user.workout_history = []

            user.workout_history.append(feedback)
            user.save()
            return Response({'status': 'Feedback recorded', 'message': 'Future workouts will be adapted.'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)


class WorkoutExplanationAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = get_auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)

        today_index = datetime.now().weekday()  # 0 = Monday
        if not user.weekly_plan or today_index >= len(user.weekly_plan):
            return Response({'explanation': "No plan generated yet."})

        today_workout = user.weekly_plan[today_index]
        goal = user.goal

        prompt = f"""
        Act as a professional fitness coach.
        User Goal: {goal}
        Today's Workout Focus: {today_workout.focus}
        Exercises: {', '.join([e.name for e in today_workout.exercises])}

        Explain broadly in 1-2 sentences why this specific workout helps achieve the goal.
        Be encouraging and scientific but simple.
        """

        try:
            from ai.utils import generate_fitty_response
            explanation = generate_fitty_response(prompt)
        except Exception:
            explanation = f"Since your goal is {goal}, today's focus on {today_workout.focus} is designed to optimize your progress!"

        return Response({'explanation': explanation})


# ============================================================================
# ADMIN
# ============================================================================
class AdminUserListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if getattr(request.user, 'role', 'USER') != 'ADMIN':
            return Response({"error": "Admin access required"}, status=403)

        users = User.objects.all().order_by('-created_at')
        data = []
        for u in users:
            data.append({
                "id": str(u.id),
                "name": u.name or u.username,
                "email": u.email,
                "role": u.role,
                "status": "Active" if u.is_active else "Blocked",
                "last_login": u.last_login.strftime("%Y-%m-%d %H:%M") if hasattr(u, 'last_login') and u.last_login else "Never",
                "created_at": u.created_at.strftime("%Y-%m-%d")
            })

        return Response(data)


class AdminUserRoleView(APIView):
    permission_classes = [permissions.AllowAny]

    def put(self, request, id):
        if getattr(request.user, 'role', 'USER') != 'ADMIN':
            return Response({"error": "Admin access required"}, status=403)

        u = User.objects(id=id).first()
        if not u:
            return Response({"error": "User not found"}, status=404)

        action = request.data.get('action')  # 'change_role', 'toggle_status', 'delete'

        if action == 'change_role':
            new_role = request.data.get('role')
            if new_role in ['USER', 'GYM_OWNER', 'ADMIN']:
                u.role = new_role
                u.save()
            else:
                return Response({"error": "Invalid role"}, status=400)

        elif action == 'toggle_status':
            u.is_active = not u.is_active
            u.save()

        elif action == 'delete':
            u.delete()
            return Response({"success": True, "message": "User deleted"})

        return Response({"success": True})