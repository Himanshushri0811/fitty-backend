import os
from google import genai
from django.conf import settings
from datetime import datetime
from accounts.models import User
import json

# Configure API Key
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    api_key = getattr(settings, 'GEMINI_API_KEY', getattr(settings, 'GOOGLE_API_KEY', None))

DEFAULT_MODEL = "gemini-2.0-flash"

def get_gemini_client():
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class FittyUnifiedService:
    @staticmethod
    def get_user_context(user):
        """
        Fetches user goal, level, and last workout for context injection.
        """
        goal = user.goal or "General fitness"
        level = user.fitness_level or "Beginner"
        
        last_workout = "None recorded yet. Encourage the user to start their first workout!"
        if hasattr(user, 'workout_history') and user.workout_history:
            # Get the last feedback entry
            last = user.workout_history[-1]
            last_workout = f"Completed workout on {last.date.strftime('%Y-%m-%d')}. Difficulty: {last.difficulty}, fatigue level: {last.fatigue_level}/10."

        return {
            "goal": goal,
            "level": level,
            "lastWorkout": last_workout
        }

    @staticmethod
    def generate_response(user, message, history=None):
        client = get_gemini_client()
        if not client:
            return "System Error: AI Brain missing API Key.", None

        context = FittyUnifiedService.get_user_context(user)
        
        system_prompt = f"""You are Fitty, a smart, friendly, and professional fitness AI coach.

Rules:
* Only answer fitness, workout, diet, posture, and health-related questions.
* If user greets → reply short and friendly.
* If question is unrelated → politely redirect to fitness topics.

Style:
* Keep responses short (max 2–3 lines)
* Use a motivating gym trainer tone
* Always give actionable advice (sets, reps, tips)

User Context:
Goal: {context['goal']}
Level: {context['level']}
Last Workout: {context['lastWorkout']}

Examples:
User: hello
→ 'Hey! Ready to train today? 💪'

User: how to build chest
→ 'Do push-ups and bench press (3×10). Focus on form and control.'

User: what's going on
→ 'All set 💪 Let’s get your workout started.'"""

        try:
            # Format history for Gemini SDK
            gemini_history = []
            if history:
                for msg in history:
                    gemini_history.append({
                        "role": "user" if msg['role'] == 'user' else "model",
                        "parts": [{"text": msg['content']}]
                    })

            chat = client.chats.create(
                model=DEFAULT_MODEL,
                config={
                    "system_instruction": system_prompt,
                },
                history=gemini_history
            )
            
            response = chat.send_message(message)
            reply_text = response.text.strip()

            # Attempt to structured response if possible (Conceptual - following requirement 6)
            # We don't force JSON here to keep the 2-3 line rule simple, 
            # but we can return a dictionary that the view can use.
            
            return reply_text, context

        except Exception as e:
            error_str = str(e)
            print(f"Fitty Unified Service Error: {error_str}")
            
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                return "Bhai, mera daily quota khatam ho gaya hai! 😅 Kal subah fir se energy ke saath milte hain, ya Gemini Pro check kar lo!", context
                
            return "Bhai, thoda dimaag hang ho gaya mera. Ek second baad fir se bol na!", context
