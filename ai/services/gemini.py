import os
import google.generativeai as genai
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

if api_key:
    genai.configure(api_key=api_key)

DEFAULT_MODEL = "gemini-1.5-flash"

def generate_chat_response(session, user_message, user):
    """
    Generates a response from Gemini, maintaining session history and injecting context.
    """
    if not api_key:
        return "System Error: AI Brain missing API Key."

    try:
        # 1. Build System Context
        system_instruction = build_system_context(user)
        
        # 2. Format History for Gemini
        # Gemini expects history excluding the current new message in start_chat, 
        # OR we can just append previous messages.
        gemini_history = []
        for msg in session.messages:
            # Map 'system' role if we stored it, though Gemini 1.5 uses system_instruction separate.
            # We only send user/model roles in history.
            if msg.role in ['user', 'model']:
                gemini_history.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [msg.content]
                })

        # 3. Create Model with System Prompt
        model = genai.GenerativeModel(
            model_name=DEFAULT_MODEL,
            system_instruction=system_instruction
        )

        # 4. Start Chat Session
        chat = model.start_chat(history=gemini_history)
        
        # 5. Send User Message
        response = chat.send_message(user_message)
        
        return response.text.strip()

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "I'm having trouble connecting to the network instantly. Please try again explicitly."

def get_posture_feedback(workout, exercise, status, issue=None):
    """
    Generates short feedback for posture correction.
    """
    if not api_key:
        return "Focus on good form and keep going!"

    prompt = f"""You are Fitty.
User doing: {exercise} ({workout})
Status: {status}
Issue: {issue or 'None'}

Give 1-2 sentences of motivating feedback."""
    
    try:
        model = genai.GenerativeModel(DEFAULT_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Posture Feedback Error: {e}")
        return "Keep your form strict and core engaged!"
