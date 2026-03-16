import os
import logging
import requests
from google import genai
from google.genai import types
from django.conf import settings

# Import prompt safely
try:
    from fitty_ai.prompts import FITTY_SYSTEM_PROMPT
except ImportError:
    FITTY_SYSTEM_PROMPT = "You are Fitty, a fitness trainer. Respond in the user's language."

logger = logging.getLogger(__name__)

def generate_fitty_response(user_message, chat_history):
    """
    Super-fast Fitty Service with Gemini -> Groq Fallback.
    Solves 429 Quota errors and ensures low latency (1-2s).
    """
    
    # 1. Try Gemini (1.5 Flash has better free quota than 2.0)
    try:
        # Clear conflicts and get key
        if "GOOGLE_API_KEY" in os.environ:
            os.environ.pop("GOOGLE_API_KEY")
            
        gemini_key = getattr(settings, 'GEMINI_API_KEY', os.getenv("GEMINI_API_KEY"))
        
        if gemini_key:
            client = genai.Client(api_key=gemini_key)
            
            formatted_history = []
            for entry in chat_history:
                role = "user" if entry["role"] == "user" else "model"
                formatted_history.append(types.Content(
                    role=role,
                    parts=[types.Part(text=entry["content"])]
                ))

            config = types.GenerateContentConfig(
                system_instruction=FITTY_SYSTEM_PROMPT,
                max_output_tokens=100,
                temperature=0.7,
            )

            # Use 1.5 Flash for better stability on free tier
            chat = client.chats.create(
                model='gemini-1.5-flash',
                config=config,
                history=formatted_history
            )
            response = chat.send_message(user_message)
            return response.text.strip()
            
    except Exception as gemini_err:
        logger.warning(f"⚠️ Gemini Failed (Quota or Error): {gemini_err}. Switching to Groq...")

    # 2. Fallback to Groq (Super Fast, No Gemini Quota Limits)
    try:
        groq_key = os.getenv("GROQ_API_KEY") or getattr(settings, 'GROQ_API_KEY', None)
        if groq_key:
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            # Prepare messages for Groq (OpenAI format)
            messages = [{"role": "system", "content": FITTY_SYSTEM_PROMPT}]
            for entry in chat_history:
                messages.append({"role": "assistant" if entry["role"] == "model" else "user", "content": entry["content"]})
            messages.append({"role": "user", "content": user_message})

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            
            resp = requests.post(url, json=payload, headers=headers, timeout=5)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Groq API Error: {resp.text}")
    except Exception as groq_err:
        logger.error(f"Groq Fallback Failed: {groq_err}")

    # 3. Last Resort: Friendly Static Error
    return "Champ, I'm currently having a small technical glitch. Let's try again in a second! Keep going!"
