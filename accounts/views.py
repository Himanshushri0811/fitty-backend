from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, GymOwner, WorkoutDay, WorkoutExercise, WorkoutFeedback
from .authentication import generate_jwt
# import razorpay (Moved to inside method to prevent pkg_resources startup crash)
from django.conf import settings
from datetime import datetime
import mongoengine
from mongoengine.queryset.visitor import Q
import random
from .workout_plans import DEFAULT_WORKOUT_PLANS
from ai.utils import get_gemini_response # Assuming this exists or similar util
import os
import logging

logger = logging.getLogger(__name__)

class HealthCheckView(APIView):
    def get(self, request):
        try:
            mongoengine.get_db().command('ping')
            return Response({"mongo": "connected", "status": "ok"})
        except Exception as e:
            return Response({"mongo": "error", "message": str(e)}, status=503)

class SignupAPIView(APIView):
    def post(self, request):
        try:
            data = request.data
            email = data.get('email', '').strip().lower()
            password = data.get('password')
            name = data.get('name', '').strip()
            
            # Determine role
            role = data.get('role')
            if not role:
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
            if User.objects(Q(email=email) | Q(username=username)).first():
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
                if data.get('age'): user.age = int(data.get('age'))
                user.gender = data.get('gender', '')

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
        except Exception as e:
            logger.error(f"Signup Error: {str(e)}", exc_info=True)
            return Response({'error': 'Internal Server Error. Please contact support.'}, status=500)


class LoginAPIView(APIView):
    def post(self, request):
        identifier = request.data.get('username', '').strip().lower()
        password = request.data.get('password')

        if not identifier or not password:
            return Response({'error': 'Credentials required'}, status=400)

        # Unified Login Logic
        # Case-insensitive search requires regex or collation, but here we enforce lower on input.
        # If we stored mixed case, we'd need __iexact.
        # We used __iexact to be safe.
        user = User.objects(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()

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

from rest_framework import status, permissions

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)
        
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
            # User specific fields
            'age': getattr(user, 'age', None),
            'gender': getattr(user, 'gender', ''),
            'height': getattr(user, 'height', None),
            'weight': getattr(user, 'weight', None),
            'goal': getattr(user, 'goal', ''),
            'fitness_level': getattr(user, 'fitness_level', 'Beginner'),
            'workouts_completed': getattr(user, 'workouts_completed', 0),
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
        editable_fields = ['name', 'age', 'gender', 'height', 'weight', 'goal', 'fitness_level', 'bio', 'gym_address', 'gym_name']
        
        for field in editable_fields:
            if field in data:
                val = data[field]
                if field in ['age', 'height', 'weight'] and val == "":
                    val = None
                setattr(user, field, val)
        
        user.save()
        return self.get(request) 

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class UploadProfilePicView(APIView):
    def post(self, request):
        user = request.user
        if not user:
             return Response({'error': 'Unauthorized'}, status=401)
        
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
            filename = f"users/{user.id}/{'cover' if is_cover else 'avatar'}_{int(datetime.now().timestamp())}.{ext}"
            
            # Save file
            path = default_storage.save(filename, ContentFile(file_obj.read()))
            file_url = settings.MEDIA_URL + path
            
            # Update user model
            if is_cover:
                user.cover_pic = file_url
            else:
                user.profile_pic = file_url
            user.save()
            
            return Response({
                'status': 'success', 
                'profile_pic': user.profile_pic,
                'cover_pic': user.cover_pic
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class VerifyPaymentAPIView(APIView):
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
            explanation = get_gemini_response(prompt)
        except:
             explanation = f"Since your goal is {goal}, today's focus on {today_workout.focus} is designed to optimize your progress!"
        
        return Response({'explanation': explanation})
