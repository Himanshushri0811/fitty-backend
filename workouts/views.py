from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.conf import settings
from ai.services.gemini import generate_workout_plan_json # New AI service
from .models import WorkoutPlan, DailyRoutine, WorkoutExercise, Exercise, PostureRule, ExerciseVideo
from .serializers import WorkoutPlanSerializer, ExerciseSerializer

import json
from datetime import datetime
import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from bson import ObjectId

class GenerateWorkoutPlanView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = request.user
        data = request.data
        
        # 1. Prepare User Profile for AI
        # Merge request data with stored user profile data if not provided
        # (Assuming User Profile model has some of this, but for now trusting the form data)
        user_profile = {
            "age": data.get("age"),
            "gender": data.get("gender"),
            "height": data.get("height"),
            "weight": data.get("weight"),
            "goal": data.get("goal"),
            "experience": data.get("experience_level"),
            "equipment": data.get("equipment", []),
            "injuries": data.get("injuries"),
            "days_available": data.get("days_per_week", 5)
        }

        # 2. Call AI Service
        try:
            ai_plan = generate_workout_plan_json(user_profile)
            if not ai_plan:
                return Response({"error": "Failed to generate plan securely. Please try again."}, status=503)
        except Exception as e:
            return Response({"error": f"AI Service Error: {str(e)}"}, status=500)

        # 3. Save to Database (MongoEngine)
        try:
            # Check if user wants to replace existing plan or just generate a draft?
            # For simplicity, we create a new active plan.
            
            new_plan = WorkoutPlan(
                user_id=str(user.id),
                name=ai_plan.get("plan_name", "AI Custom Plan"),
                goal=user_profile["goal"],
                experience_level=user_profile["experience"],
                days_per_week=int(user_profile["days_available"]),
                equipment_available=user_profile["equipment"],
                is_active=True
            )

            # Deactivate old plans for this user
            WorkoutPlan.set_active(str(user.id), None) # Deactivate all first
            
            # Build Routine Structure
            routines = []
            for day_data in ai_plan.get("days", []):
                exercises = []
                for ex_data in day_data.get("exercises", []):
                    # Try to match with existing Exercise DB for Video linkage
                    # Normalize name for search? For now strict match or simple contains
                    # db_exercise = Exercise.objects(name__icontains=ex_data['name']).first()
                    # ex_id = str(db_exercise.id) if db_exercise else None
                    
                    w_exercise = WorkoutExercise(
                        exercise_name=ex_data.get("name"),
                        exercise_id=None, # populated later if robust matching exists
                        sets=int(ex_data.get("sets", 3)),
                        reps=str(ex_data.get("reps", "12")),
                        rest_time_seconds=int(ex_data.get("rest", 60)),
                        notes=ex_data.get("notes", "")
                    )
                    exercises.append(w_exercise)

                routine = DailyRoutine(
                    day_name=day_data.get("day_name"),
                    focus_area=day_data.get("focus_area", "Rest"),
                    exercises=exercises
                )
                routines.append(routine)
            
            new_plan.routines = routines
            new_plan.save() # This generates the ID
            
            # Re-activate just this one (mongoengine save keeps is_active=True)
            # Ensure others are false
            WorkoutPlan.objects(user_id=str(user.id), id__ne=new_plan.id).update(set__is_active=False)

            # Serialize and Return
            serializer = WorkoutPlanSerializer(new_plan)
            # Manual mapping for non-DRF model
            return Response({
                "message": "Plan generated successfully!",
                "plan": {
                    "id": str(new_plan.id),
                    "name": new_plan.name,
                    "goal": new_plan.goal,
                    "routines": serializer.data['routines'] # Re-use nested serializer logic if compatible, or just dump JSON
                }
            }, status=201)

        except Exception as e:
            print(f"DB Save Error: {e}")
            return Response({"error": "Failed to save plan to database."}, status=500)


class ActiveWorkoutPlanView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user_id = str(request.user.id)
        plan = WorkoutPlan.objects(user_id=user_id, is_active=True).first()
        
        if not plan:
            return Response({"message": "No active plan found.", "plan": None})
            
        # Serialize manually to include Exercise metadata (Video URL)
        plan_data = {
            "id": str(plan.id),
            "name": plan.name,
            "goal": plan.goal,
            "experience_level": plan.experience_level,
            "days_per_week": plan.days_per_week,
            "routines": []
        }
        
        for routine in plan.routines:
            routine_data = {
                "day_name": routine.day_name,
                "focus_area": routine.focus_area,
                "exercises": []
            }
            for ex in routine.exercises:
                # Fetch video URL from Exercise DB on the fly
                # Optimization: Cache this or populate earlier
                db_ex = Exercise.objects(name__iexact=ex.exercise_name).first()
                if not db_ex:
                    # Fallback partial match search
                    db_ex = Exercise.objects(name__icontains=ex.exercise_name.split()[0]).first()
                
                ex_data = {
                    "name": ex.exercise_name,
                    "sets": ex.sets,
                    "reps": ex.reps,
                    "rest": ex.rest_time_seconds,
                    "notes": ex.notes,
                    "video_url": db_ex.video_url if db_ex else None,
                    "thumbnail": db_ex.thumbnail_url if db_ex else None,
                    "posture_config": db_ex.posture_rules if db_ex else None
                }
                routine_data["exercises"].append(ex_data)
            
            plan_data["routines"].append(routine_data)
            
        return Response({"plan": plan_data})

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
                        "keypoints": r.keypoints,
                        "min": r.min_val,
                        "max": r.max_val,
                        "message": r.message
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
                rules = []
                for r in data['posture_rules']:
                    rules.append(PostureRule(
                        name=r['name'],
                        message=r.get('message', {}),
                        check_type=r.get('check_type', 'angle'),
                        keypoints=r.get('keypoints', []),
                        min_val=float(r.get('min', 0)),
                        max_val=float(r.get('max', 360))
                    ))
                ex.posture_rules = rules
            
            ex.save()
            return Response({"message": "Exercise created", "id": str(ex.id)}, status=201)
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
        ex.description = data.get('description', ex.description) # Fix attribute
        if 'video_url' in data:
            ex.video_url = data['video_url'] # Allow clearing if passed as empty string
            
        ex.target_muscle_group = data.get('target_muscle_group', ex.target_muscle_group)
        
        # Posture Rules update
        if 'posture_config' in data:
            rules = []
            for r in data['posture_config']:
                 rules.append(PostureRule(
                    name=r.get('name'),
                    # Simplification for demo
                    keypoints=r.get('keypoints', []),
                    min_val=float(r.get('min', 0)),
                    max_val=float(r.get('max', 360)),
                    message=r.get('message', {})
                ))
            ex.posture_rules = rules

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
            
            # Generate unique filename/public_id for Cloudinary
            # Format: videos/exercise_name_uuid
            ext = video_file.name.split('.')[-1]
            safe_name = "".join([c for c in ex.name if c.isalnum() or c in (' ', '_')]).rstrip().replace(" ", "_").lower()
            public_id = f"videos/{safe_name}_{uuid.uuid4().hex[:6]}"
            
            # Native Cloudinary Upload (Robust)
            # Use 'resource_type="video"' explicitly!
            upload_result = cloudinary.uploader.upload(
                video_file, 
                public_id=public_id, 
                resource_type="video",
                overwrite=True
            )
            
            # Get HTTPS URL
            full_url = upload_result.get('secure_url')
            # public_id is returned by Cloudinary (may include folder)
            saved_public_id = upload_result.get('public_id')
            
            # Create ExerciseVideo Record
            video_record = ExerciseVideo(
                exercise=ex,
                video_url=full_url,
                cloudinary_public_id=saved_public_id,
                uploaded_by=str(user.id),
                status='Uploaded'
            )
            video_record.save()
            
            # Update Exercise for direct access (Backward Compatibility)
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
        
        # Try to convert id to ObjectId if possible
        obj_id = None
        try:
             obj_id = ObjectId(id)
        except:
             pass
        
        video = None
        if obj_id:
            # Try finding by Video ID
            try:
                video = ExerciseVideo.objects(id=obj_id).first()
            except:
                pass
            
            # Try finding by Exercise ID if not found (reference check)
            if not video:
                try:
                    video = ExerciseVideo.objects(exercise=obj_id).first()
                except:
                    pass
        
        # If still not found, try to resolve exercise by name using the raw string id
        # ... (Name lookup logic) ...
        # If we have an exercise ID (obj_id) but no video record, check the Exercise itself for legacy URL
        if not video and obj_id:
             try:
                 ex = Exercise.objects(id=obj_id).first()
                 if ex and ex.video_url:
                     # Found legacy video URL on exercise, just clear it
                     ex.video_url = None
                     ex.save()
                     return Response({"message": "Legacy video url cleared successfully"})
             except Exception as legacy_e:
                 print(f"Legacy clear error: {legacy_e}")

        if not video:
            print(f"delete failed: video not found for id {id}")
            return Response({"error": "Video not found", "id_received": id}, status=404)
            
        try:
            # Delete from Cloudinary
            if video.cloudinary_public_id:
                try:
                    import cloudinary.uploader
                    cloudinary.uploader.destroy(video.cloudinary_public_id, resource_type="video")
                except Exception as cloud_e:
                    print(f"Cloudinary delete warning: {cloud_e}")
            
            # Update Exercise reference
            if video.exercise:
                video.exercise.video_url = None
                video.exercise.save()
                
            # Delete Record
            video.delete()
            
            return Response({"message": "Video deleted successfully"})
        except Exception as e:
            return Response({"error": f"Deletion failed: {str(e)}"}, status=500)

class AdminExerciseVideoReplaceView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Replace existing video for an exercise
        user = request.user
        if getattr(user, 'role', 'USER') != 'ADMIN':
             return Response({"error": "Unauthorized: Admins only"}, status=403)
             
        exercise_id = request.data.get('exercise_id')
        video_file = request.FILES.get('video')
        
        if not exercise_id or not video_file:
             return Response({"error": "Missing exercise_id or video"}, status=400)
             
        # Find existing video
        try:
            # Find Video by Exercise Reference
            # Need strict exercise object lookup
            ex = None
            try:
                if ObjectId.is_valid(exercise_id):
                    ex = Exercise.objects(id=exercise_id).first()
            except:
                pass
                
            if not ex:
                 # Try name lookup
                 ex = Exercise.objects(name__iexact=exercise_id).first()
            
            if not ex:
                return Response({"error": "Exercise not found"}, status=404)

            # Find video record linked to this exercise
            video_record = ExerciseVideo.objects(exercise=ex.id).first()
            
            if video_record:
                # Delete old file
                if video_record.cloudinary_public_id:
                    try:
                        import cloudinary.uploader
                        cloudinary.uploader.destroy(video_record.cloudinary_public_id, resource_type="video")
                    except:
                        pass # Ignore delete error
                video_record.delete()
                
            # Now call Upload Logic (Reuse or Duplicate)
            # For simplicity, I'll essentially duplicate the upload logic or call it if I refactored.
            # I'll just run the upload flow here.
            
            ex = Exercise.objects(id=exercise_id).first()
            if not ex:
                return Response({"error": "Exercise not found"}, status=404)
            
            import cloudinary.uploader
            
            # Generate unique filename/public_id for Cloudinary
            # Format: videos/exercise_name_uuid
            ext = video_file.name.split('.')[-1]
            safe_name = "".join([c for c in ex.name if c.isalnum() or c in (' ', '_')]).rstrip().replace(" ", "_").lower()
            public_id = f"videos/{safe_name}_{uuid.uuid4().hex[:6]}"
            
            # Native Cloudinary Upload (Robust)
            # Use 'resource_type="video"' explicitly!
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
             
        day = request.query_params.get('day') # Optional
        
        # Helper to map Day -> Muscle Group (optional logic)
        # If day is provided, we can filter.
        # But commonly Admin wants to see ALL exercises to manage videos.
        # Or filters by day if we have a schedule.
        # Let's return all exercises with their video status.
        
        exercises = Exercise.objects.all()
        
        # Optional Day Filter (Naive implementation based on common splits)
        # Monday: Chest, Tuesday: Back, etc?
        # If user strictly wants filtering by day, we need a map.
        # For now, if day is specified, I'll filter by some logic or just return all with day meta if applicable.
        # Since Exercise doesn't have "Day", we return all. 
        # But the prompt says "Show list of days -> On selecting a day -> Show all exercises".
        # This implies the FRONTEND manages the grouping or I should provide it.
        # I'll provide a grouped list or just valid list.
        
        # Let's try to filter if muscle group matches common splits to be helpful.
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
                # Filter in memory or query
                exercises = [e for e in exercises if e.target_muscle_group in targets or any(t in e.target_muscle_group for t in targets)]
        
        data = []
        for ex in exercises:
            # Check video status
            # Only 1 video per exercise supported for now
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
