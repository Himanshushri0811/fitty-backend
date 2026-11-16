"""
Claude Diet Chat Views — FitMitra
API endpoints for Claude-powered diet conversations.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import DietProfile
from ai.services.claude_diet import get_diet_response, generate_quick_diet_plan


def get_user_context(user) -> dict:
    """
    Builds the user context dict from DB for the AI prompt.
    """
    try:
        profile = DietProfile.objects(user=user).first()
    except Exception:
        profile = None

    name = getattr(user, 'name', '') or getattr(user, 'username', 'Friend')
    goal = profile.goal if profile else "Maintenance"
    diet_type = profile.diet_type if profile else "Veg"
    target_calories = profile.target_calories if profile else 2000
    target_protein = profile.target_protein if profile else 150
    allergies = list(profile.allergies) if profile and profile.allergies else []
    budget_level = profile.budget_level if profile else "Medium"

    return {
        "name": name,
        "goal": goal,
        "diet_type": diet_type,
        "target_calories": target_calories,
        "target_protein": target_protein,
        "allergies": allergies,
        "budget_level": budget_level,
    }


class ClaudeDietChatView(APIView):
    """
    POST /api/diet/claude-chat/

    Body:
    {
        "message": "User message here",
        "history": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }

    Response:
    {
        "reply": "AI response",
        "provider": "claude" | "groq" | "error",
        "model": "model-name"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        message = request.data.get("message", "").strip()
        history = request.data.get("history", [])

        if not message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Build user context
        user_context = get_user_context(request.user)

        # Validate and sanitize history
        sanitized_history = []
        for msg in history:
            if isinstance(msg, dict) and msg.get("role") in ("user", "assistant") and msg.get("content"):
                sanitized_history.append({
                    "role": msg["role"],
                    "content": str(msg["content"])[:2000]  # Cap length per message
                })

        # Keep last 20 messages max (10 turns) to stay within context limits
        if len(sanitized_history) > 20:
            sanitized_history = sanitized_history[-20:]

        # Get AI response
        result = get_diet_response(user_context, sanitized_history, message)

        return Response(result, status=status.HTTP_200_OK)


class ClaudeDietPlanView(APIView):
    """
    POST /api/diet/claude-plan/
    Generates a full 7-day meal plan using Claude.
    No body required — uses user's saved profile.

    Response:
    {
        "plan": "Full meal plan text in markdown",
        "user_context": { ... }
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        user_context = get_user_context(request.user)
        plan_text = generate_quick_diet_plan(user_context)

        return Response({
            "plan": plan_text,
            "user_context": user_context,
        }, status=status.HTTP_200_OK)


class ClaudeDietSuggestionsView(APIView):
    """
    GET /api/diet/claude-suggestions/
    Returns 5 smart quick-action diet questions tailored to the user.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        user_context = get_user_context(request.user)
        goal = user_context.get("goal", "Maintenance")
        diet_type = user_context.get("diet_type", "Veg")
        budget = user_context.get("budget_level", "Medium")

        # Goal-based smart suggestions
        suggestions_map = {
            "Weight Loss": [
                f"Mere liye best 1200 calorie {diet_type} meal plan banao",
                "Kya roti band karni chahiye weight loss mein?",
                "Best fat-burning Indian breakfast kya hai?",
                "Dinner mein kya khana chahiye weight loss ke liye?",
                "Intermittent fasting kaise shuru karoon?",
            ],
            "Muscle Gain": [
                f"High protein {diet_type} meal plan for muscle gain banao",
                "Post-workout kya khana best hai?",
                "Budget mein protein kaise badhayein?",
                "Dal vs paneer — konsa better hai muscle ke liye?",
                "Whey protein lena chahiye ya nahi?",
            ],
            "Maintenance": [
                f"Balanced 7-day {diet_type} meal plan banao",
                "Healthy Indian snacks kaun se hain?",
                "Weekend cheat meal kaise manage karein?",
                "Metabolism badhane ke liye kya khayein?",
                "Water intake aur nutrition kaise balance karein?",
            ],
        }

        suggestions = suggestions_map.get(goal, suggestions_map["Maintenance"])

        return Response({
            "suggestions": suggestions,
            "user_context": {
                "goal": goal,
                "diet_type": diet_type,
                "budget_level": budget,
            }
        })
