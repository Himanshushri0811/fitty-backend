from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import datetime
from .models import FittyConversation
from ai.services.fitty_service import generate_fitty_response
import logging

logger = logging.getLogger(__name__)

class FittyAgentView(APIView):
    """
    Endpoint for interacting with Fitty AI Agent.
    POST /api/fitty-agent/
    Request Body: { "message": "Fitty target weight loss" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user_message = request.data.get("message")

        if not user_message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Fetch recent conversation history (last 5 pairs)
            # We use simple dicts instead of LangChain objects for speed
            history_objs = FittyConversation.objects(user=user).order_by('-timestamp')[:5]
            chat_history = []
            
            # Reverse to get chronological order [oldest -> newest]
            for h in reversed(list(history_objs)):
                chat_history.append({"role": "user", "content": h.message})
                chat_history.append({"role": "model", "content": h.response})

            # 2. Process with Optimized Fitty Service (1-3s response)
            agent_response = generate_fitty_response(user_message, chat_history)

            # 3. Save to database
            FittyConversation(
                user=user,
                message=user_message,
                response=agent_response
            ).save()

            return Response({
                "status": "success",
                "response": agent_response,
                "timestamp": datetime.utcnow()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_str = str(e)
            logger.error(f"🔴 Fitty Agent View Error: {error_str}")
            
            # Quota handling (if not caught by service)
            if "429" in error_str or "quota" in error_str.lower():
                return Response({
                    "error": "Quota Exceeded",
                    "response": "Champ, I'm currently handling too many fans right now! 😅 Could you wait about 20 seconds and try again?",
                    "detail": "Gemini API quota exceeded."
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            return Response({
                "error": error_str,
                "response": "I'm having a small brain freeze right now. Let's try that again in a second!",
                "detail": "Failed to process message with Fitty AI"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
