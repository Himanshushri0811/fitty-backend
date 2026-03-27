from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import datetime
from .models import FittyConversation
# import moved inside post to prevent boot overload
import logging

logger = logging.getLogger(__name__)

class FittySessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        pipeline = [
            {"$match": {"user": user.id}},
            {"$sort": {"timestamp": 1}},
            {"$group": {
                "_id": "$session_id",
                "title": {"$first": "$message"},
                "updated_at": {"$last": "$timestamp"}
            }},
            {"$sort": {"updated_at": -1}}
        ]
        try:
            result = list(FittyConversation.objects.aggregate(*pipeline))
            sessions = [{"id": str(i["_id"]), "title": (str(i["title"])[:30] + '...') if len(str(i["title"])) > 30 else str(i["title"])} for i in result if i.get("_id")]
            return Response(sessions, status=200)
        except Exception as e:
            return Response([{"id": "fitty_main", "title": "Main Fitty Chat"}], status=200)

class FittySessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id):
        user = request.user
        try:
            # Delete all messages related to this session
            deleted_count = FittyConversation.objects(user=user, session_id=session_id).delete()
            if deleted_count > 0:
                return Response({"status": "success", "message": "Session deleted"}, status=status.HTTP_200_OK)
            return Response({"error": "Session not found or already deleted"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FittyAgentView(APIView):
    """
    Endpoint for interacting with Fitty AI Agent.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Fetch chat history so frontend can display saved messages"""
        user = request.user
        session_id = request.query_params.get("session_id", "fitty_main")
        
        # Get last 50 messages for this specific session
        history_objs = FittyConversation.objects(user=user, session_id=session_id).order_by('-timestamp')[:50]
        
        chat_history = []
        for h in reversed(list(history_objs)):
            chat_history.append({"role": "user", "content": h.message, "timestamp": h.timestamp})
            chat_history.append({"role": "model", "content": h.response, "timestamp": h.timestamp})
            
        return Response({
            "session_id": session_id,
            "history": chat_history
        }, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        user_message = request.data.get("message")
        mode = request.data.get("mode", "CHAT")
        session_id = request.data.get("session_id", "fitty_main")

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

            # 2. Process with Langchain Tool Agent
            from .agent import process_fitty_message
            agent_response = process_fitty_message(str(user.id), user_message, chat_history, mode)

            # 3. Save to database
            FittyConversation(
                user=user,
                session_id=session_id,
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
