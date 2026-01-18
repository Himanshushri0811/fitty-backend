import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# ==================== ENV SETUP ====================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env files
print(f"Loading .env files from: {BASE_DIR}")
load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR / '.env.local')

# Try both variable names
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# DEBUG: print exactly what is loaded
print(f"DEBUG: Loaded API key (raw) = {repr(api_key)}")

if not api_key:
    print("❌ ERROR: GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables")
else:
    # Configure Gemini ONCE at module level
    genai.configure(api_key=api_key.strip())
    print("✅ Gemini API configured successfully")

# Default model
DEFAULT_MODEL = 'models/gemini-flash-latest'

# ==================== INTENT CLASSIFICATION ====================
def classify_query_intent(user_message):
    message_lower = user_message.lower()
    is_hindi = bool(re.search(r'[\u0900-\u097F]', user_message))
    
    patterns = {
        'workout_plan': [
            r'gym.*plan', r'workout.*plan', r'exercise.*plan', r'रूटीन',
            r'monday.*saturday', r'weekly.*schedule', r'plan.*batao'
        ],
        'exercise_technique': [
            r'how.*to', r'कैसे.*करें', r'tips', r'technique', r'form',r'correct.*form'
        ],
        'nutrition_plan': [
            r'diet', r'खाना', r'nutrition', r'meal', r'क्या.*खाएं'
        ],
        'home_workout': [
            r'home.*workout', r'without.*equipment', r'घर.*पर'
        ]
    }
    
    for intent, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return {'intent': intent, 'language': 'hindi' if is_hindi else 'english'}
    
    return {'intent': 'general', 'language': 'hindi' if is_hindi else 'english'}

# ==================== RESPONSE CLEANING ====================
def clean_response(text):
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ==================== FALLBACKS ====================
def get_structured_fallback(intent_info, user_message):
    lang = intent_info['language']
    if lang == 'hindi':
        return "मुझे खेद है, मैं अभी कनेक्ट नहीं कर पा रहा हूँ. कृपया थोड़ी देर बाद प्रयास करें."
    return "I'm having trouble connecting right now. Please try again in a moment."

# ==================== MAIN GENERATION ====================
def get_gemini_response(user_message, user_goal="general fitness", history=None, context=None):
    print(f"\n🎯 Processing: {user_message[:50]}...")
    
    # DEBUG: check API key before every request
    print(f"DEBUG: Using API key (stripped) = {repr(api_key.strip() if api_key else None)}")
    
    if not user_goal: user_goal = "general fitness"

    intent_info = classify_query_intent(user_message)
    language = intent_info['language']
    page_context = f"- Current Page: {context.get('page', 'Unknown')}" if context else ""

    prompt = f"""You are Fitty, also known as FitMitra — a friendly, reliable, and production-ready fitness AI assistant.

IDENTITY & PERSONA:
* Your name is Fitty. Always refer to yourself as Fitty.
* You are friendly, motivating, and supportive.
* Your tone is warm, encouraging, and natural.

SCOPE OF HELP:
* Gym & Home workouts
* Exercise form guides
* Fat loss & Muscle gain basics
* Simple diet tips (Non-medical)
* Motivation & Discipline

STRICT LIMITATIONS:
* NO medical advice.
* NO steroids/drugs.
* NO non-fitness topics.

RESPONSE STYLE:
* Friendly, short paragraphs.
* If Voice Mode: Max 2-3 sentences.

ENDING RULE:
End with a short encouraging line or a fitness question.

USER CONTEXT:
- Goal: {user_goal}
- Query: "{user_message}"
- Language: {language}
{page_context}

RESPOND IN {language.upper()} LANGUAGE.
"""

    if not api_key:
        print("❌ ERROR: API key missing, returning fallback")
        return get_structured_fallback(intent_info, user_message)

    try:
        model = genai.GenerativeModel(DEFAULT_MODEL)
        response = model.generate_content(prompt)
        print("✅ Gemini response received successfully")
        return clean_response(response.text)
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return get_structured_fallback(intent_info, user_message)

# ==================== POSTURE FEEDBACK ====================
def get_posture_feedback(workout, exercise, status, issue=None):
    if not api_key:
        print("❌ API key missing in posture feedback")
        return "Focus on good form and keep going!"

    prompt = f"""You are Fitty.
User doing: {exercise} ({workout})
Status: {status}
Issue: {issue or 'None'}

Give 1-2 sentences of motivating feedback.
"""
    try:
        model = genai.GenerativeModel("models/gemini-flash-latest")
        response = model.generate_content(prompt)
        print("✅ Posture feedback generated successfully")
        return response.text.strip()
    except Exception as e:
        print(f"❌ Posture Feedback Error: {e}")
        return "Keep your form strict and core engaged!"
