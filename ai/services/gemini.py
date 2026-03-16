import os
from google import genai
from django.conf import settings
from .context_builder import build_system_context
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly to ensure key is found
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent # FITMITRA root
load_dotenv(BASE_DIR / '.env')

# Configure API Key
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    # try settings if env var not picked up directly
    api_key = getattr(settings, 'GEMINI_API_KEY', getattr(settings, 'GOOGLE_API_KEY', None))

DEFAULT_MODEL = "gemini-2.0-flash"

def get_gemini_client():
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def generate_chat_response(session, user_message, user):
    """
    Generates a response from Gemini, maintaining session history and injecting context.
    """
    client = get_gemini_client()
    if not client:
        return "System Error: AI Brain missing API Key."

    try:
        # 1. Build System Context
        system_instruction = build_system_context(user)
        
        # 2. Format History for Gemini
        gemini_history = []
        for msg in session.messages:
            if msg.role in ['user', 'model']:
                gemini_history.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [{"text": msg.content}]
                })

        # 3. Use Chat Session with the new SDK
        chat = client.chats.create(
            model=DEFAULT_MODEL,
            config={
                "system_instruction": system_instruction,
            },
            history=gemini_history
        )
        
        # 4. Send User Message
        response = chat.send_message(user_message)
        
        return response.text.strip()

    except Exception as e:
        print(f"Gemini API Error (services/gemini.py): {e}")
        return "I'm having trouble connecting to the network instantly. Please try again explicitly."

def get_posture_feedback(workout, exercise, status, issue=None):
    """
    Generates short feedback for posture correction.
    """
    client = get_gemini_client()
    if not client:
        return "Focus on good form and keep going!"

    prompt = f"""You are Fitty.
User doing: {exercise} ({workout})
Status: {status}
Issue: {issue or 'None'}

Give 1-2 sentences of motivating feedback."""
    
    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Posture Feedback Error: {e}")
        return "Keep your form strict and core engaged!"

def generate_workout_plan_json(user_profile):
    """
    Generates a full 7-day workout plan in JSON format based on user profile.
    """
    import json
    
    client = get_gemini_client()
    if not client:
        return None

    # Construct the Prompt
    prompt = f"""
    You are an expert fitness trainer AI named Fitty.
    Create a personalized 7-day workout plan for this user:
    
    - Age: {user_profile.get('age', 'N/A')}
    - Gender: {user_profile.get('gender', 'N/A')}
    - Height: {user_profile.get('height', 'N/A')}
    - Weight: {user_profile.get('weight', 'N/A')}
    - Goal: {user_profile.get('goal', 'General Fitness')}
    - Experience Level: {user_profile.get('experience', 'Beginner')}
    - Equipment Available: {', '.join(user_profile.get('equipment', ['None']))}
    - Injuries/Limitations: {user_profile.get('injuries', 'None')}
    - Days Per Week: {user_profile.get('days_available', 7)}

    CRITICAL INSTRUCTIONS:
    1. Return ONLY valid JSON. No markdown, no explanations.
    2. The JSON structure must be exactly:
    {{
        "plan_name": "Short catchy name for the plan",
        "goal_summary": "Brief explanation of why this plan works",
        "days": [
            {{
                "day_name": "Monday",
                "focus_area": "Chest & Triceps",
                "exercises": [
                    {{
                        "name": "Exercise Name",
                        "sets": 3,
                        "reps": "12",
                        "rest": 60,
                        "notes": "Tip for form"
                    }}
                ]
            }},
            ... (for all 7 days, use 'Rest' for rest days)
        ]
    }}
    3. Ensure exercises match the equipment available.
    4. Vary the rep ranges based on the goal (e.g., lower reps for strength, higher for endurance).
    5. Include 7 days explicitly (Monday to Sunday).
    """

    try:
        # Use Controlled Generation for JSON
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            }
        )
        
        # Parse JSON
        plan_data = json.loads(response.text)
        return plan_data
        
    except Exception as e:
        print(f"Workout Generation Error: {e}")
        return None
