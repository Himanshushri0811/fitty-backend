import difflib
import json
import logging
import os
import re
import uuid
from datetime import datetime
from bson import ObjectId

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.workout_plans import DEFAULT_WORKOUT_PLANS
from ai.services.gemini import generate_workout_plan_json
from .models import WorkoutPlan, DailyRoutine, WorkoutExercise, Exercise, PostureRule, ExerciseVideo
from .serializers import WorkoutPlanSerializer, ExerciseSerializer

logger = logging.getLogger(__name__)

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


# ============================================================================
# HELPERS
# ============================================================================
def _auth_user(request):
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'id', None):
        return None
    return user


def _to_int(value, default, lo, hi):
    """'3-4' -> 3, '60s' -> 60, None -> default. Hamesha lo..hi ke beech."""
    m = re.search(r'\d+', str(value)) if value is not None else None
    n = int(m.group()) if m else default
    return max(lo, min(hi, n))


def _txt(value, default='', max_len=200):
    if value is None:
        return default
    s = str(value).strip()
    return s[:max_len] if s else default


def _as_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() not in ('false', '0', 'no', '')
    return bool(value)


def _as_list(value):
    if isinstance(value, str):
        return [v.strip() for v in value.split(',') if v.strip()]
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return []


def _norm(name):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', (name or '').lower())).strip()


def _load_library():
    """Poori Exercise library ek hi query me. {normalized_name: Exercise}"""
    return {_norm(ex.name): ex for ex in Exercise.objects()}


def _match_exercise(name, library):
    key = _norm(name)
    if key in library:
        return library[key]
    close = difflib.get_close_matches(key, list(library.keys()), n=1, cutoff=0.8)
    return library[close[0]] if close else None


def _rule_to_dict(rule):
    return {
        'name': rule.name,
        'check_type': rule.check_type,
        'keypoints': list(rule.keypoints or []),
        'min': rule.min_val,
        'max': rule.max_val,
        'message': dict(rule.message or {}),
    }


def _build_rules(raw_rules):
    rules = []
    for r in raw_rules or []:
        if not isinstance(r, dict):
            continue
        try:
            keypoints = [int(k) for k in (r.get('keypoints') or [])]
            lo = float(r.get('min', r.get('min_val', 0)))
            hi = float(r.get('max', r.get('max_val', 180)))
        except (TypeError, ValueError):
            raise ValueError('keypoints, min aur max numbers hone chahiye')

        check_type = str(r.get('check_type') or 'angle')
        if check_type in ('angle', 'angle_range') and len(keypoints) != 3:
            raise ValueError('Angle rule me exactly 3 keypoints chahiye, jaise [11, 13, 15]')

        # Angle 0..180 hota hai
        lo, hi = max(0.0, min(lo, 180.0)), max(0.0, min(hi, 180.0))
        if lo > hi:
            lo, hi = hi, lo

        message = r.get('message')
        rules.append(PostureRule(
            name=str(r.get('name') or 'Rule')[:60],
            check_type=check_type,
            keypoints=keypoints,
            min_val=lo,
            max_val=hi,
            message=message if isinstance(message, dict) else {},
        ))
    return rules


def build_routines(days, library):
    """AI / template / user, teeno ka data yahin se safe ho kar WorkoutPlan me jaata hai."""
    routines = []
    for i, d in enumerate((days or [])[:7]):
        if not isinstance(d, dict):
            continue
        exercises = []
        for ex in (d.get('exercises') or [])[:12]:
            if not isinstance(ex, dict):
                continue
            raw_name = _txt(ex.get('name') or ex.get('exercise_name'), '', 80)
            if not raw_name:
                continue
            match = _match_exercise(raw_name, library)
            exercises.append(WorkoutExercise(
                exercise_name=match.name if match else raw_name,
                exercise_id=str(match.id) if match else None,
                sets=_to_int(ex.get('sets'), 3, 1, 10),
                reps=_txt(ex.get('reps'), '12', 20),
                rest_time_seconds=_to_int(ex.get('rest', ex.get('rest_time_seconds')), 60, 0, 600),
                notes=_txt(ex.get('notes') or ex.get('description'), '', 300),
            ))
        routines.append(DailyRoutine(
            day_name=_txt(d.get('day_name'), DAY_NAMES[i % 7], 20),
            focus_area=_txt(d.get('focus_area') or d.get('focus'), 'Full Body', 60),
            exercises=exercises,
        ))
    if not routines:
        raise ValueError('Plan me kam se kam 1 din chahiye')
    return routines


def serialize_routines(routines, library):
    out = []
    for r in routines:
        items = []
        for ex in r.exercises:
            db_ex = library.get(_norm(ex.exercise_name))
            items.append({
                'name': ex.exercise_name,
                'exercise_id': ex.exercise_id or (str(db_ex.id) if db_ex else None),
                'sets': ex.sets,
                'reps': ex.reps,
                'rest': ex.rest_time_seconds,
                'notes': ex.notes,
                'video_url': db_ex.video_url if db_ex else None,
                'thumbnail': db_ex.thumbnail_url if db_ex else None,
                'muscle': db_ex.target_muscle_group if db_ex else None,
                'posture_config': [_rule_to_dict(p) for p in db_ex.posture_rules] if db_ex else [],
            })
        out.append({'day_name': r.day_name, 'focus_area': r.focus_area, 'exercises': items})
    return out


def serialize_plan(plan, library):
    return {
        'id': str(plan.id),
        'name': plan.name,
        'goal': plan.goal,
        'experience_level': plan.experience_level,
        'days_per_week': plan.days_per_week,
        'routines': serialize_routines(plan.routines, library),
    }


def _template_days(goal, days):
    goal_l = (goal or '').lower()
    template = None
    for key, val in DEFAULT_WORKOUT_PLANS.items():
        if goal_l and (key.lower() in goal_l or goal_l in key.lower()):
            template = val
            break
    template = template or DEFAULT_WORKOUT_PLANS['Hybrid / All-Round Fitness']
    return [d for d in template if d.get('exercises')][:days]


def _try_ai(profile):
    try:
        plan = generate_workout_plan_json(profile)
        if isinstance(plan, str):
            plan = json.loads(plan)
        days = plan.get('days') if isinstance(plan, dict) else None
        if days:
            return _txt(plan.get('plan_name'), 'AI Custom Plan', 60), days
    except Exception:
        logger.warning('AI workout generation failed', exc_info=True)
    return None


def _activate_only(user_id, plan):
    WorkoutPlan.objects(user_id=user_id, id__ne=plan.id).update(set__is_active=False)


# ============================================================================
# POST /generate/   (AI se banao; "save": false => sirf preview)
# ============================================================================
class GenerateWorkoutPlanView(APIView):
    """
    Body (sab optional, missing ho to user profile se bharta hai):
    goal, experience_level, days_per_week, duration_min, equipment[], focus[],
    injuries, age, gender, height, weight, save (default true)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        user = _auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)

        d = request.data
        profile = {
            'age': d.get('age') or getattr(user, 'age', None),
            'gender': d.get('gender') or getattr(user, 'gender', None),
            'height': d.get('height') or getattr(user, 'height', None),
            'weight': d.get('weight') or getattr(user, 'weight', None),
            'goal': _txt(d.get('goal') or getattr(user, 'goal', None), 'General Fitness', 60),
            'experience': _txt(d.get('experience_level') or getattr(user, 'fitness_level', None), 'Beginner', 20),
            'equipment': _as_list(d.get('equipment')),
            'injuries': _txt(d.get('injuries') or ', '.join(getattr(user, 'medical_conditions', None) or []), '', 150) or None,
            'days_available': _to_int(d.get('days_per_week'), 5, 1, 7),
            'duration_min': _to_int(d.get('duration_min'), 45, 15, 120),
            'focus': _as_list(d.get('focus')),
        }
        should_save = _as_bool(d.get('save'), True)

        library = _load_library()

        candidates = []
        ai = _try_ai(profile)
        if ai:
            candidates.append(('ai', ai[0], ai[1]))
        candidates.append(('template', f"{profile['goal']} Plan",
                           _template_days(profile['goal'], profile['days_available'])))

        routines, source, plan_name = None, None, None
        for source, plan_name, days in candidates:
            try:
                routines = build_routines(days, library)
                break
            except Exception:
                logger.warning('build_routines failed for source=%s', source, exc_info=True)
        if routines is None:
            return Response({'error': 'Workout generate nahi ho paya. Thodi der baad try karo.'}, status=500)

        if not should_save:
            return Response({
                'message': 'Preview ready',
                'source': source,
                'saved': False,
                'plan': {
                    'name': plan_name,
                    'goal': profile['goal'],
                    'experience_level': profile['experience'],
                    'days_per_week': len(routines),
                    'routines': serialize_routines(routines, library),
                },
            })

        try:
            plan = WorkoutPlan(
                user_id=str(user.id),
                name=plan_name,
                goal=profile['goal'],
                experience_level=profile['experience'],
                days_per_week=len(routines),
                equipment_available=profile['equipment'],
                routines=routines,
                is_active=True,
            )
            plan.save()                      # pehle naya save
            _activate_only(str(user.id), plan)  # phir baaki deactivate
        except Exception as e:
            logger.error('Saving generated plan failed', exc_info=True)
            return Response({'error': 'Plan save nahi hua', 'details': str(e)}, status=500)

        return Response({
            'message': 'Plan generated successfully!',
            'source': source,
            'saved': True,
            'plan': serialize_plan(plan, library),
        }, status=201)


# ============================================================================
# GET /current/
# ============================================================================
class ActiveWorkoutPlanView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = _auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)
        try:
            plan = WorkoutPlan.objects(user_id=str(user.id), is_active=True).order_by('-created_at').first()
            if not plan:
                return Response({'message': 'No active plan found.', 'plan': None})
            return Response({'plan': serialize_plan(plan, _load_library())})
        except Exception as e:
            logger.error('Active plan load failed', exc_info=True)
            return Response({'error': 'Plan load nahi hua', 'details': str(e)}, status=500)


# ============================================================================
# POST /save/  -> naya plan (manual ya AI-preview edit ke baad) active banao
# PUT  /save/  -> active plan ko edit karo (din/exercise add, delete, reorder)
# Body: {"name": "...", "goal": "...", "routines": [ {day_name, focus_area, exercises:[{name,sets,reps,rest,notes}]} ]}
# ============================================================================
class SaveWorkoutPlanView(APIView):
    permission_classes = [AllowAny]

    def _routines_from(self, data):
        return build_routines(data.get('routines') or data.get('plan'), _load_library())

    def post(self, request):
        user = _auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)
        try:
            routines = self._routines_from(request.data)
            plan = WorkoutPlan(
                user_id=str(user.id),
                name=_txt(request.data.get('name'), 'My Custom Plan', 60),
                goal=_txt(request.data.get('goal') or getattr(user, 'goal', None), '', 60),
                experience_level=_txt(getattr(user, 'fitness_level', None), 'Beginner', 20),
                days_per_week=len(routines),
                routines=routines,
                is_active=True,
            )
            plan.save()
            _activate_only(str(user.id), plan)
            return Response({'message': 'Plan saved', 'plan': serialize_plan(plan, _load_library())}, status=201)
        except ValueError as ve:
            return Response({'error': str(ve)}, status=400)
        except Exception as e:
            logger.error('Save plan failed', exc_info=True)
            return Response({'error': 'Plan save nahi hua', 'details': str(e)}, status=500)

    def put(self, request):
        user = _auth_user(request)
        if not user:
            return Response({'error': 'Unauthorized'}, status=401)
        plan = WorkoutPlan.objects(user_id=str(user.id), is_active=True).order_by('-created_at').first()
        if not plan:
            return Response({'error': 'Koi active plan nahi hai'}, status=404)
        try:
            if request.data.get('routines') or request.data.get('plan'):
                plan.routines = self._routines_from(request.data)
                plan.days_per_week = len(plan.routines)
            if 'name' in request.data:
                plan.name = _txt(request.data.get('name'), plan.name, 60)
            plan.save()
            return Response({'message': 'Plan updated', 'plan': serialize_plan(plan, _load_library())})
        except ValueError as ve:
            return Response({'error': str(ve)}, status=400)
        except Exception as e:
            logger.error('Update plan failed', exc_info=True)
            return Response({'error': 'Plan update nahi hua', 'details': str(e)}, status=500)


# ============================================================================
# GET /library/?muscle=Chest&q=press   (hallka: exercise picker + video search)
# ============================================================================
class ExerciseLibraryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Exercise.objects()
        muscle = request.query_params.get('muscle')
        q = request.query_params.get('q')
        if muscle:
            qs = qs.filter(target_muscle_group__iexact=muscle)
        if q:
            qs = qs.filter(name__icontains=q)
        return Response([{
            'id': str(ex.id),
            'name': ex.name,
            'muscle': ex.target_muscle_group,
            'equipment': ex.equipment_type,
            'difficulty': ex.difficulty,
            'video_url': ex.video_url,
            'thumbnail': ex.thumbnail_url,
            'has_posture_check': bool(ex.posture_rules),
        } for ex in qs.order_by('name')[:100]])


# ============================================================================
# EXERCISE LIST & DETAIL VIEWS
# ============================================================================
class ExerciseListView(APIView):
    permission_classes = [AllowAny] # Or Admin User only for editing

    def get(self, request):
        exercises = Exercise.objects.all()
        data = []
        for ex in exercises:
            data.append({
                "id": str(ex.id),
                "name": ex.name,
                "muscle": ex.target_muscle_group,
                "equipment": ex.equipment_type,
                "video_url": ex.video_url,
                "posture_config": [
                    {
                        "name": r.name,
                        "check_type": r.check_type,
                        "keypoints": list(r.keypoints or []),
                        "min": r.min_val,
                        "max": r.max_val,
                        "message": dict(r.message or {})
                    } for r in ex.posture_rules
                ]
            })
        return Response(data)

    def post(self, request):
        if getattr(request.user, 'role', 'USER') != 'ADMIN':
             return Response({"error": "Unauthorized: Admins only"}, status=403)

        data = request.data
        try:
            ex = Exercise(
                name=data['name'],
                description=data.get('description', ''),
                video_url=data.get('video_url', ''),
                difficulty=data.get('difficulty', 'Beginner'),
                target_muscle_group=data.get('target_muscle_group', 'Full Body'),
                equipment_type=data.get('equipment_type', 'None')
            )
            # Posture Rules
            if 'posture_rules' in data:
                ex.posture_rules = _build_rules(data['posture_rules'])
            
            ex.save()
            return Response({"message": "Exercise created", "id": str(ex.id)}, status=201)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class ExerciseDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, id):
        try:
            return Exercise.objects.get(id=id)
        except Exception:
            return None

    def put(self, request, id):
        if getattr(request.user, 'role', 'USER') != 'ADMIN':
             return Response({"error": "Unauthorized: Admins only"}, status=403)

        ex = self.get_object(id)
        if not ex:
            return Response({"error": "Not Found"}, status=404)
        
        data = request.data
        ex.name = data.get('name', ex.name)
        ex.description = data.get('description', ex.description)
        if 'video_url' in data:
            ex.video_url = data['video_url'] # Allow clearing if passed as empty string
            
        ex.target_muscle_group = data.get('target_muscle_group', ex.target_muscle_group)
        
        rules_in = data.get('posture_config', data.get('posture_rules'))
        if rules_in is not None:
            try:
                ex.posture_rules = _build_rules(rules_in)
            except ValueError as ve:
                return Response({"error": str(ve)}, status=400)

        ex.save()
        return Response({"message": "Updated Successfully"}, status=200)

    def delete(self, request, id):
        if getattr(request.user, 'role', 'USER') != 'ADMIN':
             return Response({"error": "Unauthorized: Admins only"}, status=403)
             
        ex = self.get_object(id)
        if ex:
            ex.delete()
            return Response({"success": True})
        return Response({"error": "Not Found"}, status=404)


# =========================================================================
# ADMIN VIDEO MANAGEMENT
# =========================================================================

class AdminExerciseVideoUploadView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        user = request.user
        if getattr(user, 'role', 'USER') != 'ADMIN':
             return Response({"error": "Unauthorized: Admins only"}, status=403)

        exercise_id = request.data.get('exercise_id') # Can be ID or Name
        video_file = request.FILES.get('video')
        
        if not exercise_id or not video_file:
            return Response({"error": "Missing exercise_id or video file"}, status=400)
            
        ex = None
        try:
             ex = Exercise.objects(id=exercise_id).first()
        except:
             pass
        
        if not ex:
             ex = Exercise.objects(name__iexact=exercise_id).first()
             
        if not ex:
             # Auto-create exercise if it doesn't exist (robust for fixed plan)
             try:
                 ex = Exercise(
                     name=exercise_id, 
                     target_muscle_group="Full Body",
                     equipment_type="None",
                     difficulty="Beginner",
                     description="Auto-created by Video Upload"
                 )
                 ex.save()
             except Exception as e:
                 return Response({"error": f"Failed to auto-create exercise '{exercise_id}': {str(e)}"}, status=500)
             
        try:
            import cloudinary.uploader
            
            ext = video_file.name.split('.')[-1]
            safe_name = "".join([c for c in ex.name if c.isalnum() or c in (' ', '_')]).rstrip().replace(" ", "_").lower()
            public_id = f"videos/{safe_name}_{uuid.uuid4().hex[:6]}"
            
            upload_result = cloudinary.uploader.upload(
                video_file, 
                public_id=public_id, 
                resource_type="video",
                overwrite=True
            )
            
            full_url = upload_result.get('secure_url')
            saved_public_id = upload_result.get('public_id')
            
            video_record = ExerciseVideo(
                exercise=ex,
                video_url=full_url,
                cloudinary_public_id=saved_public_id,
                uploaded_by=str(user.id),
                status='Uploaded'
            )
            video_record.save()
            
            ex.video_url = full_url
            ex.save()
            
            return Response({
                "message": "Video uploaded successfully",
                "video_url": full_url,
                "exercise": ex.name,
                "video_id": str(video_record.id)
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": "Failed to save video", "details": str(e)}, status=500)


class AdminExerciseVideoDeleteView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, id):
        user = request.user
        if getattr(user, 'role', 'USER') != 'ADMIN':
             return Response({"error": "Unauthorized: Admins only"}, status=403)
        
        obj_id = None
        try:
             obj_id = ObjectId(id)
        except:
             pass
        
        video = None
        if obj_id:
            try:
                video = ExerciseVideo.objects(id=obj_id).first()
            except:
                pass
            
            if not video:
                try:
                    video = ExerciseVideo.objects(exercise=obj_id).first()
                except:
                    pass
        
        if not video and obj_id:
             try:
                 ex = Exercise.objects(id=obj_id).first()
                 if ex and ex.video_url:
                     ex.video_url = None
                     ex.save()
                     return Response({"message": "Legacy video url cleared successfully"})
             except Exception as legacy_e:
                 print(f"Legacy clear error: {legacy_e}")

        if not video:
            print(f"delete failed: video not found for id {id}")
            return Response({"error": "Video not found", "id_received": id}, status=404)
            
        try:
            if video.cloudinary_public_id:
                try:
                    import cloudinary.uploader
                    cloudinary.uploader.destroy(video.cloudinary_public_id, resource_type="video")
                except Exception as cloud_e:
                    print(f"Cloudinary delete warning: {cloud_e}")
            
            if video.exercise:
                video.exercise.video_url = None
                video.exercise.save()
                
            video.delete()
            return Response({"message": "Video deleted successfully"})
        except Exception as e:
            return Response({"error": f"Deletion failed: {str(e)}"}, status=500)


class AdminExerciseVideoReplaceView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        user = request.user
        if getattr(user, 'role', 'USER') != 'ADMIN':
             return Response({"error": "Unauthorized: Admins only"}, status=403)
             
        exercise_id = request.data.get('exercise_id')
        video_file = request.FILES.get('video')
        
        if not exercise_id or not video_file:
             return Response({"error": "Missing exercise_id or video"}, status=400)
             
        try:
            ex = None
            try:
                if ObjectId.is_valid(exercise_id):
                    ex = Exercise.objects(id=exercise_id).first()
            except:
                pass
                
            if not ex:
                 ex = Exercise.objects(name__iexact=exercise_id).first()
            
            if not ex:
                return Response({"error": "Exercise not found"}, status=404)

            video_record = ExerciseVideo.objects(exercise=ex.id).first()
            if video_record:
                if video_record.cloudinary_public_id:
                    try:
                        import cloudinary.uploader
                        cloudinary.uploader.destroy(video_record.cloudinary_public_id, resource_type="video")
                    except:
                        pass
                video_record.delete()
                
            ex = Exercise.objects(id=exercise_id).first()
            if not ex:
                return Response({"error": "Exercise not found"}, status=404)
            
            import cloudinary.uploader
            
            ext = video_file.name.split('.')[-1]
            safe_name = "".join([c for c in ex.name if c.isalnum() or c in (' ', '_')]).rstrip().replace(" ", "_").lower()
            public_id = f"videos/{safe_name}_{uuid.uuid4().hex[:6]}"
            
            upload_result = cloudinary.uploader.upload(
                video_file, 
                public_id=public_id, 
                resource_type="video",
                overwrite=True
            )
            
            full_url = upload_result.get('secure_url')
            saved_public_id = upload_result.get('public_id')
            
            new_video = ExerciseVideo(
                exercise=ex,
                video_url=full_url,
                cloudinary_public_id=saved_public_id,
                uploaded_by=str(user.id),
                status='Uploaded'
            )
            new_video.save()
            
            ex.video_url = full_url
            ex.save()
            
            return Response({"message": "Video replaced successfully", "video_url": full_url})
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": f"Replace failed: {str(e)}"}, status=500)


class AdminVideoListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        if getattr(request.user, 'role', 'USER') != 'ADMIN':
             return Response({"error": "Unauthorized: Admins only"}, status=403)
             
        day = request.query_params.get('day')
        exercises = Exercise.objects.all()
        
        if day:
            day_map = {
                "Monday": ["Chest", "Tricep"],
                "Tuesday": ["Back", "Biceps"],
                "Wednesday": ["Legs", "Abs"],
                "Thursday": ["Shoulders"],
                "Friday": ["Full Body", "Cardio"],
                "Saturday": ["Full Body"],
                "Sunday": ["Rest"]
            }
            targets = day_map.get(day, [])
            if targets:
                exercises = [e for e in exercises if e.target_muscle_group in targets or any(t in e.target_muscle_group for t in targets)]
        
        data = []
        for ex in exercises:
            vid = ExerciseVideo.objects(exercise=ex).first()
            status_txt = "Uploaded" if (vid or ex.video_url) else "Pending"
            
            data.append({
                "id": str(ex.id),
                "name": ex.name,
                "muscle_group": ex.target_muscle_group,
                "video_status": status_txt,
                "video_url": ex.video_url
            })
            
        return Response(data)
