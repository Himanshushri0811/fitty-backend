import os
import google.generativeai as genai
import requests
from django.conf import settings
from .context_builder import build_system_context

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or getattr(settings, 'GEMINI_API_KEY', None)
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or getattr(settings, 'GROQ_API_KEY', None)

# Models
# Models
GEMINI_MODEL_STABLE = "gemini-1.5-flash" # Stable Free Tier
GROQ_MODEL = "llama-3.3-70b-versatile" # Updated Stable Model

class AIProvider:
    def generate(self, session, message, user):
        raise NotImplementedError

class GeminiProvider(AIProvider):
    def __init__(self):
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL_STABLE

    def generate(self, session, message, user):
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API Key missing")

        try:
            # Context
            sys_prompt = build_system_context(user)
            
            # History
            history = []
            for msg in session.messages:
                if msg.role in ['user', 'model']:
                    history.append({
                        "role": "user" if msg.role == "user" else "model",
                        "parts": [msg.content]
                    })
            
            model = genai.GenerativeModel(self.model_name, system_instruction=sys_prompt)
            chat = model.start_chat(history=history)
            response = chat.send_message(message)
            return response.text.strip()
            
        except Exception as e:
            # Categorize Gemini Errors
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                raise ResourceWarning("Gemini Quota Exceeded")
            elif "404" in error_str:
                raise RuntimeError("Gemini Model Not Found")
            else:
                raise e

class GroqProvider(AIProvider):
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, session, message, user):
        if not self.api_key:
            raise ValueError("Groq API Key missing")

        sys_prompt = build_system_context(user)
        
        # History (Groq uses OpenAI format)
        messages = [{"role": "system", "content": sys_prompt}]
        for msg in session.messages:
             if msg.role in ['user', 'model']:
                role = "assistant" if msg.role == "model" else "user"
                messages.append({"role": role, "content": msg.content})
        
        # Add current message
        messages.append({"role": "user", "content": message})

        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(self.url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data['choices'][0]['message']['content'].strip()
            elif resp.status_code == 429:
                raise ResourceWarning("Groq Quota Exceeded")
            else:
                raise RuntimeError(f"Groq API Error: {resp.text}")
        except Exception as e:
            raise e

class AIServiceRouter:
    def __init__(self):
        self.gemini = GeminiProvider()
        self.groq = GroqProvider()

    def get_response(self, session, message, user):
        # 1. Try Gemini First (Preferred)
        try:
            print(f"🤖 Calling Gemini ({GEMINI_MODEL_STABLE})...")
            return self.gemini.generate(session, message, user)
        except (ResourceWarning, RuntimeError, ValueError) as e:
            print(f"⚠️ Gemini Failed ({e}). Switching to Groq...")
            
            # 2. Fallback to Groq
            try:
                if GROQ_API_KEY:
                    print(f"🚀 Calling Groq ({GROQ_MODEL})...")
                    return self.groq.generate(session, message, user)
                else:
                    print("❌ Groq Key Missing. Cannot Fallback.")
                    raise e
            except Exception as groq_e:
                print(f"❌ Groq also failed: {groq_e}")
                # Re-raise the most relevant error or a generic one
                raise RuntimeError("All AI providers are busy or unavailable.")
