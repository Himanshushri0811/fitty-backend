import google.generativeai as genai
import os
from django.conf import settings

# List of models to try in order of preference (Newest to Oldest)
CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-1.5-flash",
    "gemini-pro"
]

_working_model = None

def get_best_gemini_model():
    """
    Iterates through available models and returns the first one that works.
    Caches the result to avoid repeated checks.
    """
    global _working_model
    
    # Return cached model if available
    if _working_model:
        return _working_model

    # Configure API
    api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        print("❌ No API Key found for Model Selection.")
        return "gemini-2.0-flash" # Default fallback
        
    genai.configure(api_key=api_key)

    print("🤖 Auto-Detecting Best Gemini Model...")
    
    for model_name in CANDIDATE_MODELS:
        try:
            print(f"   Testing: {model_name}...")
            model = genai.GenerativeModel(model_name)
            # Lightweight test
            response = model.generate_content("Hi", request_options={"timeout": 5})
            if response:
                print(f"   ✅ Model Found: {model_name}")
                _working_model = model_name
                return model_name
        except Exception as e:
            print(f"   ❌ {model_name} Failed: {str(e)[:50]}...")
            continue
            
    # If all fail, return the most likely standard one
    print("⚠️ All auto-detection failed. Defaulting to gemini-2.0-flash")
    return "gemini-2.0-flash"
