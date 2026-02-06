from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .services.gemini import generate_chat_response, get_posture_feedback
from .models import ChatSession
from .usage import check_and_increment_quota
from subscriptions.service import SubscriptionService # Ensure we don't break other refs if any

class AISessionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List all chat sessions for the user (Sidebar History).
        """
        try:
            sessions = ChatSession.objects(user=request.user).order_by('-updated_at')
            data = [
                {
                    "id": str(s.id),
                    "title": s.title or "New Chat",
                    "updated_at": s.updated_at.isoformat()
                }
                for s in sessions
            ]
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class AISessionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        """
        Delete a specific chat session.
        """
        try:
            session = ChatSession.objects(id=id, user=request.user).first()
            if not session:
                return Response({"error": "Session not found"}, status=404)
            
            session.delete()
            return Response({"success": True})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class AIChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get chat history for a session.
        If `session_id` param provided, fetch that session.
        Else, fetch the LATEST session.
        """
        try:
            user = request.user
            session_id = request.query_params.get('session_id')
            
            session = None
            if session_id:
                try:
                    session = ChatSession.objects(id=session_id, user=user).first()
                except:
                    pass # Invalid ID, fallthrough
            
            # If no ID or invalid, get latest
            if not session and not session_id:
                session = ChatSession.objects(user=user).order_by('-updated_at').first()
            
            if not session:
                return Response({"history": [], "session_id": None})
            
            history = [
                {
                    "role": m.role, 
                    "content": m.content, 
                    "timestamp": m.timestamp.isoformat()
                } 
                for m in session.messages
            ]
            
            return Response({
                "history": history, 
                "session_id": str(session.id),
                "title": session.title
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        """
        Send a message to Fitty.
        """
        try:
            user = request.user
            message = request.data.get("message")
            session_id = request.data.get("session_id")

            if not message:
                return Response({"error": "Message required"}, status=400)

            # 1. Check Quota (Backend Plan Limit)
            allowed, reason = check_and_increment_quota(user)
            if not allowed:
                return Response({
                    "reply": reason,
                    "type": "error",
                    "limit_reached": True
                }, status=403) # 403 Forbidden for Plan Limit

            # 2. Get or Create Session
            session = None
            if session_id:
                try:
                    session = ChatSession.objects(id=session_id, user=user).first()
                except:
                    session = None # Invalid ID
            
            if not session:
                # generate title from first 4 words
                words = message.split()
                title = " ".join(words[:4]) 
                if len(words) > 4:
                     title += "..."
                session = ChatSession(user=user, title=title)
                session.save()

            # 3. Add User Message
            session.add_message('user', message)

            # 4. Generate Response (Via Service Router)
            try:
                from .services.provider import AIServiceRouter
                router = AIServiceRouter()
                reply_text = router.get_response(session, message, user)
                
            except ResourceWarning:
                # Quota Exceeded on ALL Providers
                return Response({
                    "reply": "I'm currently overloaded with requests. Please try again in a minute.", 
                    "type": "error"
                }, status=429)
            except RuntimeError as re:
                # API Errors
                return Response({
                    "reply": "I'm having trouble thinking right now. Please try again.",
                    "debug_error": str(re),
                    "type": "error"
                }, status=503)
            except Exception as e:
                # General Failure
                print(f"AI Service Fatal Error: {e}")
                return Response({"error": "Service Internal Error"}, status=500)

            # 5. Save AI Response
            session.add_message('model', reply_text)

            return Response({
                "reply": reply_text,
                "session_id": str(session.id),
                "remaining_quota": 1000 - user.assistant_daily_usage if hasattr(user, 'assistant_daily_usage') else 0
            })
            
        except Exception as e:
            print(f"Chat View Fatal Error: {e}")
            return Response({"error": "Failed to process message"}, status=500)

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
