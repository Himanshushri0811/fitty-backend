from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .services.gemini import get_gemini_response, get_posture_feedback

from subscriptions.service import SubscriptionService
from gym_management.models import Member
from accounts.models import GymOwner

class AIChatAPIView(APIView):
    # TEMPORARY: AllowAny for testing (change back to IsAuthenticated later)
    permission_classes = [AllowAny]

    def post(self, request):
        message = request.data.get("message")
        
        # Get user goal from profile
        user_goal = "general fitness"
        is_gym_owner = False
        gym_context = ""

        try:
            if request.user and request.user.is_authenticated:
                if getattr(request.user, 'role', '') == 'GYM_OWNER':
                    is_gym_owner = True
                    owner = request.user
                    
                    # 1. Check Limits
                    if not SubscriptionService.can_use_assistant(owner):
                        return Response({
                            "reply": "You have reached your daily AI Assistant limit (20 queries). Upgrade to PRO for unlimited access!",
                            "type": "ai",
                            "limit_reached": True
                        }, status=200) # Status 200 so frontend displays it as a message
                    
                    # 2. Build Gym Context
                    total = Member.objects(gym_owner=owner).count()
                    paid = Member.objects(gym_owner=owner, fees_status='PAID').count()
                    pending = Member.objects(gym_owner=owner, fees_status='PENDING').count()
                    gym_context = f"""
                    CONTEXT: User is a Gym Owner named {owner.gym_name}.
                    Gym Stats: Total Members: {total}, Paid: {paid}, Pending Dues: {pending}.
                    Plan: {owner.plan_type}.
                    """
                else:
                    user_goal = getattr(request.user, 'goal', 'general fitness')
        except Exception as e:
            pass # Anonymous or error

        if not message:
            return Response({"error": "Message required"}, status=400)

        context = request.data.get("context", {})
        
        # Merge Gym Context
        if is_gym_owner:
            message = f"{gym_context}\nUser Query: {message}"

        try:
            reply = get_gemini_response(message, user_goal, context=context)
            
            # 3. Record Usage (only if successful response)
            if is_gym_owner:
                SubscriptionService.record_assistant_usage(request.user)

            return Response({
                "type": "ai",
                "reply": reply
            })
        except Exception as e:
            return Response({
                "error": f"AI service error: {str(e)}"
            }, status=500)

class PostureAnalysisAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        workout = request.data.get("workout")
        exercise = request.data.get("exercise")
        posture_status = request.data.get("posture_status")
        issue = request.data.get("issue")
        device = request.data.get("device", "desktop")

        if not workout or not exercise or not posture_status:
            return Response({"error": "Missing posture data"}, status=400)

        try:
            # Get trainer-style feedback from Gemini
            feedback = get_posture_feedback(workout, exercise, posture_status, issue)
            
            return Response({
                "device": device,
                "workout": workout,
                "exercise": exercise,
                "posture_status": posture_status,
                "issue": issue,
                "feedback": feedback
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)
