from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, GymOwner, WorkoutDay, WorkoutExercise, WorkoutFeedback
from .authentication import generate_jwt
# import razorpay (Moved to inside method to prevent pkg_resources startup crash)
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import mongoengine
from mongoengine.queryset.visitor import Q
import random
from .workout_plans import DEFAULT_WORKOUT_PLANS
# imports moved inside methods to prevent boot block
import os
import logging

logger = logging.getLogger(__name__)
    
# Import for email and UUID
from django.core.mail import send_mail
from django.conf import settings
import uuid
from datetime import timedelta

class ForgotPasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        
        # Strict Email Validation
        if not email:
            return Response({'error': 'Email is required'}, status=400)
            
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return Response({'error': 'Invalid email format'}, status=400)
        
        user = User.objects(email=email).first()
        
        # Always return 200 to prevent enumeration, but log internal state
        if not user:
            logger.info(f"Forgot password requested for non-existent email: {email}")
            return Response({'message': 'If an account exists with this email, a reset link has been sent.'}, status=200)
            
        # Generate Secure Token
        token = str(uuid.uuid4())
        
        # Set Expiry (20 minutes)
        expiry_time = datetime.utcnow() + timedelta(minutes=20)
        
        user.reset_password_token = token
        user.reset_password_expiry = expiry_time
        user.save()
        
        # Build Link
        # In production this should be settings.FRONTEND_URL. Hardcoding for dev.
        reset_link = f"https://fitty-ai.netlify.app/auth/reset-password/{token}"
        # Fallback to localhost if needed for testing, but user asked for fitty-ai.netlify.app
        # reset_link = f"http://localhost:3000/auth/reset-password/{token}" 

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
            # In a strict security audit, you might not want to return 500 here either, but for UX:
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
            
        # Reset Password
        user.set_password(new_password)
        
        # Clear Token and Expiry to prevent reuse
        user.reset_password_token = None
        user.reset_password_expiry = None
        user.save()
        
        return Response({'message': 'Password reset successfully'})


from rest_framework.permissions import AllowAny

@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        db_status = "Connected"
        try:
            # Check mongo connection
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

@method_decorator(csrf_exempt, name='dispatch')
class SignupAPIView(APIView):
    def post(self, request):
        try:
            data = request.data
            email = data.get('email', '').strip().lower()
            password = data.get('password')
            name = data.get('name', '').strip()
            
            # Determine role
            # Determine role
            role = data.get('role', 'USER')
            
            # Security: Prevent unauthorized Admin creation via API
            if role == 'ADMIN':
                return Response({'error': 'Admin accounts cannot be created via Signup API.'}, status=403)
                
            if not role or role not in ['USER', 'GYM_OWNER']:
                if 'gym_name' in data or 'gym-owner' in request.path:
                    role = 'GYM_OWNER'
                else:
                    role = 'USER'

            if not email or not password:
                return Response({'error': 'Email and password required'}, status=400)
            
            # Determine Username
            username = data.get('username')
            if username:
                username = username.strip() # maintain case for display, but check specific for query? 
                                            # actually, best to just store lowercase or verify case-insensitive uniqueness.
                                            # We will enforce lowercase for username strictness to avoid ambiguity
                username = username.lower()
            else:
                # Auto-generate username from email if not provided (common for Gym Owners)
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                while User.objects(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1

            # Check Global Uniqueness (Single Source of Truth)
            existing_user = User.objects(Q(email=email) | Q(username=username)).first()
            if existing_user:
                return Response({'error': 'Email or Username already taken'}, status=400)

            # Create User
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
                
                # Robust numeric parsing to prevent ValueError crash
                try:
                    age_val = data.get('age')
                    if age_val is not None and str(age_val).strip():
                        user.age = int(float(age_val)) # Handle float strings too
                except (ValueError, TypeError):
                    logger.warning(f"Invalid age provided: {data.get('age')}")
                
                user.gender = data.get('gender', '')
                user.mobile = data.get('mobile', '')
                user.dob = data.get('dob') # Ensure format YYYY-MM-DD or parse it
                
                # Activity Level Mapping (Frontend Terminology to Backend Choices)
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
                'user': {
                    'email': user.email, 
                    'role': user.role, 
                    'id': str(user.id),
                    'name': user.name if user.name else getattr(user, 'gym_name', user.username),
                    'username': user.username,
                    'gym_name': getattr(user, 'gym_name', None),
                    'plan': getattr(user, 'plan_type', 'FREE')
                },
                'access': tokens['access'],
                'refresh': tokens['refresh']
            }, status=201)
        except mongoengine.errors.ValidationError as ve:
            # Handle invalid email, duplicate keys, or other schema validation issues gracefully
            return Response({
                'error': 'Validation Error',
                'details': str(ve)
            }, status=400)
        except Exception as e:
            logger.error(f"Signup Error Traceback: ", exc_info=True)
            return Response({
                'error': 'Internal Server Error. Check server logs.',
                'details': str(e),
                'type': type(e).__name__
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        try:
            identifier = request.data.get('email') or request.data.get('username', '')
            identifier = str(identifier).strip().lower()
            password = str(request.data.get('password'))

            if not identifier or not password:
                return Response({'error': 'Credentials required'}, status=400)

            # --------------------------------------------------
            # FAILSAFE DEMO LOGIN (Works even if DB is down)
            # --------------------------------------------------
            is_admin_failsafe = (identifier == "anshu@fitty.com" and password == "admin@1234")
            is_test_failsafe = (identifier == "test@test.com" and password == "123456")

            if is_admin_failsafe or is_test_failsafe:
                target_email = "anshu@fitty.com" if is_admin_failsafe else "test@test.com"
                fallback_role = "ADMIN" if is_admin_failsafe else "USER"
                fallback_name = "Admin Anshu" if is_admin_failsafe else "Demo Champ (Offline)"
                fallback_username = "anshui911" if is_admin_failsafe else "demochamp"
                
                try:
                    user = User.objects(email=target_email).first()
                    if user:
                        tokens = generate_jwt(user)
                        return Response({
                            'user': {
                                'email': user.email,
                                'role': user.role,
                                'id': str(user.id),
                                'name': user.name if user.name else user.username,
                                'username': user.username,
                                'plan': getattr(user, 'plan_type', 'FREE')
                            },
                            'access': tokens['access'],
                            'refresh': tokens['refresh'],
                            'demo_mode': False
                        })
                except Exception as db_err:
                    logger.warning(f"DB Error during failsafe login search: {db_err}")

                # GENUINE TOKEN GENERATION (Even for mock user)
                tokens = generate_jwt(user_id='65e000000000000000000000', role=fallback_role)

                return Response({
                    'user': {
                        'email': target_email,
                        'role': fallback_role,
                        'id': '65e000000000000000000000', # Static BSON-like ID
                        'name': fallback_name,
                        'username': fallback_username,
                        'plan': 'PRO' if is_admin_failsafe else 'FREE'
                    },
                    'access': tokens['access'],
                    'refresh': tokens['refresh'],
                    'demo_mode': True,
                    'message': 'Logged in via Master-Key Failsafe Mode'
                }, status=200)

            # Standard Login Flow
            user = None
            try:
                user = User.objects(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
            except Exception as e:
                logger.error(f"Database Query Error during login: {e}")
                return Response({'error': 'Our database is taking a nap. Use test@test.com for demo.'}, status=503)

            if not user or not user.check_password(password):
                return Response({'error': 'Invalid Credentials'}, status=401)

            tokens = generate_jwt(user)
            return Response({
                'user': {
                    'email': user.email,
                    'role': user.role,
                    'id': str(user.id),
                    'name': user.name if user.name else getattr(user, 'gym_name', user.username),
                    'username': user.username,
                    'gym_name': getattr(user, 'gym_name', None),
                    'plan': getattr(user, 'plan_type', 'FREE')
                },
                'access': tokens['access'],
                'refresh': tokens['refresh']
            })
        except Exception as e:
            logger.error(f"Login Fatal Crash: {str(e)}", exc_info=True)
            # EXTREME FAILSAFE: Never throw a 500/502 to the browser if possible
            return Response({'error': 'System stabilization in progress. Please use demo credentials.'}, status=200) # Using 200 with error key to keep frontend alive 


from rest_framework import status, permissions

class ProfileView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)
        
        # Calculate Stats (BMI, Ideal Weight)
        bmi = None
        bmi_category = "N/A"
        ideal_weight_range = "N/A"
        
        if user.height and user.weight:
            # BMI = weight (kg) / (height (m) ^ 2)
            h_m = user.height / 100
            bmi_val = user.weight / (h_m * h_m)
            bmi = round(bmi_val, 1)
            
            if bmi < 18.5: bmi_category = "Underweight"
            elif 18.5 <= bmi < 24.9: bmi_category = "Normal"
            elif 25 <= bmi < 29.9: bmi_category = "Overweight"
            else: bmi_category = "Obese"
            
            # Simple Hamwi Formula for Ideal Weight (Approx)
            # Men: 48kg + 2.7kg per inch over 5ft
            # Women: 45.5kg + 2.2kg per inch over 5ft
            # Using simplified average for now: 22 BMI * h * h
            ideal_min = round(18.5 * h_m * h_m, 1)
            ideal_max = round(24.9 * h_m * h_m, 1)
            ideal_weight_range = f"{ideal_min} - {ideal_max} kg"

        # Build profile data
        profile_data = {
            'id': str(user.id),
            'email': user.email,
            'role': user.role,
            'name': user.name if user.name else getattr(user, 'gym_name', user.username),
            'username': getattr(user, 'username', ''),
            'profile_pic': getattr(user, 'profile_pic', ''),
            'cover_pic': getattr(user, 'cover_pic', ''),
            'plan': getattr(user, 'plan_type', 'FREE'),
            'bio': getattr(user, 'bio', ''),
            
            # Core Stats
            'age': getattr(user, 'age', None),
            'gender': getattr(user, 'gender', ''),
            'height': getattr(user, 'height', None),
            'weight': getattr(user, 'weight', None),
            'goal': getattr(user, 'goal', ''),
            'fitness_level': getattr(user, 'fitness_level', 'Beginner'),
            
            # Extended Fields (Phase 1)
            'target_weight': getattr(user, 'target_weight', None),
            'activity_level': getattr(user, 'activity_level', 'Moderately Active'),
            'diet_preference': getattr(user, 'diet_preference', 'Non-Vegetarian'),
            'medical_conditions': getattr(user, 'medical_conditions', []),
            'allergies': getattr(user, 'allergies', []),
            'preferred_workout_type': getattr(user, 'preferred_workout_type', 'Gym'),
            'mobile': getattr(user, 'mobile', ''),
            'dob': getattr(user, 'dob', None),

            # Calculated Stats
            'bmi': bmi,
            'bmi_category': bmi_category,
            'ideal_weight_range': ideal_weight_range,
            
            # Gamification
            'workouts_completed': getattr(user, 'workouts_completed', 0),
            'current_streak': 0, # Placeholder for now, can implement real logic
            'calories_burned': sum(log.calories_burned for log in getattr(user, 'daily_calories_log', [])),
            
            # GymOwner specific
            'gym_name': getattr(user, 'gym_name', ''),
            'gym_address': getattr(user, 'gym_address', '')
        }
        
        return Response(profile_data)

    def put(self, request):
        user = request.user
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)

        data = request.data
        
        # Update allowed fields
        editable_fields = [
            'name', 'age', 'gender', 'height', 'weight', 'goal', 
            'fitness_level', 'bio', 'gym_address', 'gym_name', 
            'mobile', 'dob', 'activity_level', 
            'target_weight', 'diet_preference', 'preferred_workout_type'
        ]
        
        # Lists need special handling if we want to replace or append, here we replace
        list_fields = ['medical_conditions', 'allergies']

        for field in editable_fields:
            if field in data:
                val = data[field]
                if field in ['age', 'height', 'weight', 'target_weight'] and val == "":
                    val = None
                setattr(user, field, val)
        
        for field in list_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Log weight history if weight changed
        if 'weight' in data and data['weight']:
            try:
                new_weight = float(data['weight'])
                # avoid duplicates for same day? For now just append.
                # In robust app, check if today's log exists.
                # Assuming WeightLog is imported
                from .models import WeightLog
                user.weight_history.append(WeightLog(weight=new_weight, date=datetime.utcnow()))
            except:
                pass
        
        user.save()
        return self.get(request)
 

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class UploadProfilePicView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = request.user
        
        file_obj = request.FILES.get('profile_pic') or request.FILES.get('cover_pic')
        is_cover = 'cover_pic' in request.FILES
        
        if not file_obj:
            return Response({'error': 'No file uploaded'}, status=400)
        
        # Basic validation (size, type)
        if file_obj.size > 5 * 1024 * 1024:
             return Response({'error': 'File too large (max 5MB)'}, status=400)
             
        try:
            # Generate unique filename
            ext = file_obj.name.split('.')[-1]
            timestamp = int(datetime.now().timestamp())
            prefix = 'cover' if is_cover else 'avatar'
            
            # Using forward slashes is generally safer in Django storage regardless of OS
            filename = f"users/{str(user.id)}/{prefix}_{timestamp}.{ext}"
            
            # Save file
            path = default_storage.save(filename, ContentFile(file_obj.read()))
            
            # Ensure path is always forward-slashed for URL construction
            web_path = path.replace('\\', '/')
            file_url = settings.MEDIA_URL + web_path
            
            # Update user model
            if is_cover:
                user.cover_pic = file_url
            else:
                user.profile_pic = file_url
                
            user.save()
            logger.info(f"User {user.id} uploaded {'cover' if is_cover else 'profile'} pic: {file_url}")
            
            return Response({
                'status': 'success', 
                'profile_pic': user.profile_pic,
                'cover_pic': user.cover_pic
            })
        except Exception as e:
            logger.error(f"File Upload Error for user {getattr(user, 'id', 'Unknown')}: {str(e)}", exc_info=True)
            return Response({'error': 'Internal Server Error during upload'}, status=500)

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
            
            if request.user and request.user.role == 'GYM_OWNER':
                request.user.update_plan('PRO')
                return Response({'status': 'Payment Verified', 'plan': 'PRO'})
            return Response({'error': 'User mismatch'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class UserWorkoutPlanAPI(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        user = request.user
        if not user or user.role != 'USER':
             return Response({'error': 'Unauthorized'}, status=401)
        
        force_refresh = request.query_params.get('force', 'false') == 'true'
        
        # 1. Generate/Regenerate Plan
        if force_refresh or not user.weekly_plan:
            # Determine template based on goal
            goal = user.goal or "Hybrid / All-Round Fitness"
            template = DEFAULT_WORKOUT_PLANS.get(goal)
            
            if not template:
                # Fuzzy match
                for key in DEFAULT_WORKOUT_PLANS.keys():
                    if key.lower() in goal.lower() or goal.lower() in key.lower():
                        template = DEFAULT_WORKOUT_PLANS[key]
                        break
                if not template:
                    template = DEFAULT_WORKOUT_PLANS["Hybrid / All-Round Fitness"]

            # Create new plan structure
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

        # 2. Adaptive Logic (Reducing sets if fatigued)
        response_plan = []
        recent_feedbacks = user.workout_history[-3:] if user.workout_history else []
        high_fatigue_count = sum(1 for f in recent_feedbacks if f.fatigue_level >= 8)
        poor_form_count = sum(1 for f in recent_feedbacks if f.form_quality == 'Poor')
        scale_down = high_fatigue_count > 0 or poor_form_count > 0
        
        for day in user.weekly_plan:
            # Serialize
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
                
                # Auto-detect local video if no custom URL is set
                if not ex_dict['video_url']:
                    # Sanitize name: "Bench Press" -> "Bench_Press.mp4"
                    filename = ex.name.replace(" ", "_").replace("/", "_") + ".mp4"
                    local_path = os.path.join(settings.MEDIA_ROOT, 'exercises', filename)
                    if os.path.exists(local_path):
                        relative_url = f"{settings.MEDIA_URL}exercises/{filename}"
                        ex_dict['video_url'] = request.build_absolute_uri(relative_url)
                
                # Apply Adaptive Logic if needed (Reducing Volume)
                if scale_down and day_is_today:
                     # Parse sets/reps if possible, or just append a note
                     try:
                         if 'sets' in ex_dict and str(ex_dict['sets']).isdigit():
                             current_sets = int(ex_dict['sets'])
                             if current_sets > 2:
                                 ex_dict['sets'] = str(current_sets - 1)
                                 ex_dict['adaptive_note'] = "Reduced volume due to recent fatigue."
                     except:
                         pass
                
                day_dict['exercises'].append(ex_dict)
            response_plan.append(day_dict)

        return Response(response_plan)
    
    def put(self, request):
        """Allow editing a specific day's focus or exercises"""
        user = request.user
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)
            
        data = request.data
        # Expecting { day_index: 0, focus: "New Focus", exercises: [...] }
        day_index = data.get('day_index')
        
        if day_index is None or not (0 <= day_index < 7):
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

class WorkoutFeedbackAPI(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user = request.user
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
            # Ensure list initialized
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
        user = request.user
        if not user: return Response({'error': 'Unauthorized'}, status=401)
        
        # Get today's workout
        today_index = datetime.now().weekday() # 0=Mon
        if not user.weekly_plan:
            return Response({'explanation': "No plan generated yet."})
            
        today_workout = user.weekly_plan[today_index]
        goal = user.goal
        
        # Generate prompt
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
            
        action = request.data.get('action') # 'change_role', 'toggle_status', 'delete'
        
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
