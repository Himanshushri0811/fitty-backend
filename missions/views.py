import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Mission, MissionProgress, UserStats
from ai.services.fitty_mission_generator import FittyMissionGenerator

class TodayMissionView(APIView):
    def get(self, request):
        user_id = str(request.user.id)
        today_str = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        
        # Check if mission exists today
        mission = Mission.objects(user_id=user_id, date_assigned=today_str).first()
        
        # Get or create UserStats
        stats = UserStats.objects(user_id=user_id).first()
        if not stats:
            stats = UserStats(user_id=user_id).save()
            
        if not mission:
            # Generate new mission
            recent_progress = MissionProgress.objects(user_id=user_id, status='completed').order_by('-completed_at').first()
            recent_mission = recent_progress.mission_id if recent_progress else None

            # Gen via AI
            ai_plan = FittyMissionGenerator.generate_daily_mission(
                level=stats.level,
                last_mission=recent_mission
            )
            
            # Save
            mission = Mission(
                user_id=user_id,
                title=ai_plan.get('title', 'Daily Protocol'),
                difficulty=ai_plan.get('difficulty', 'Beginner'),
                exercises=ai_plan.get('exercises', []),
                xp_reward=ai_plan.get('xp_reward', 100),
                ai_strategy_message=ai_plan.get('ai_strategy_message', 'Initiating...'),
                date_assigned=today_str
            ).save()
            
            # Create tracking
            MissionProgress(user_id=user_id, mission_id=mission, status='pending').save()

        # Build payload
        return Response({
            "mission": {
                "id": str(mission.id),
                "title": mission.title,
                "difficulty": mission.difficulty,
                "strategy": mission.ai_strategy_message,
                "exercises": mission.exercises,
                "xp_reward": mission.xp_reward,
            },
            "stats": {
                "level": stats.level,
                "xp": stats.xp,
                "streak": stats.streak_days
            }
        })

class CompleteMissionView(APIView):
    def post(self, request, mission_id):
        user_id = str(request.user.id)
        today_str = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        
        from bson import ObjectId
        try:
            mission_oid = ObjectId(mission_id)
        except:
            return Response({"error": "Invalid mission ID format"}, status=status.HTTP_400_BAD_REQUEST)

        progress = MissionProgress.objects(user_id=user_id, mission_id=mission_oid, status='pending').first()
        if not progress:
            return Response({"error": "Mission not found or already completed"}, status=status.HTTP_400_BAD_REQUEST)
            
        mission = progress.mission_id
        
        # Completing mission
        progress.status = 'completed'
        progress.completed_at = datetime.datetime.utcnow()
        progress.save()

        # Update stats
        stats = UserStats.objects(user_id=user_id).first()
        if not stats:
            stats = UserStats(user_id=user_id).save()

        stats.xp += mission.xp_reward
        stats.level = int(stats.xp / 500) + 1
        
        # Streak logic
        yesterday_str = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        if stats.last_mission_date == yesterday_str:
            stats.streak_days += 1
        elif stats.last_mission_date != today_str:
            stats.streak_days = 1
            
        stats.last_mission_date = today_str
        stats.save()

        return Response({
            "message": "Mission Completed",
            "xp_earned": mission.xp_reward,
            "new_xp_total": stats.xp,
            "new_level": stats.level,
            "streak": stats.streak_days
        })
