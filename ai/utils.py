import os
from google import genai
from django.conf import settings

def generate_fitty_response(user_message):
    """
    Tiered Reliability: Gemini 1.5 -> Groq -> Local Error Msg
    """
    try:
        # TIER 1: GEMINI
        from google import genai
        api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY'))
        if api_key:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=user_message,
            )
            if response and response.text:
                return response.text
    except Exception as gemini_err:
        print(f"Tier 1 (Gemini) Error: {gemini_err}")

    try:
        # TIER 2: GROQ
        from groq import Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            client = Groq(api_key=groq_key)
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": user_message}],
                model="llama-3.3-70b-versatile",
            )
            if completion.choices[0].message.content:
                return completion.choices[0].message.content
    except Exception as groq_err:
        print(f"Tier 2 (Groq) Error: {groq_err}")

    return "Fitty is currently doing some heavy lifting! 🏋️ Try again in a few seconds, Champ!"


def detect_query_intent(query):
    """
    Detect what the user is asking about
    """
    query_lower = query.lower()
    
    intent_map = {
        'pushup': any(word in query_lower for word in ['pushup', 'push up', 'पुश']),
        'pullup': any(word in query_lower for word in ['pullup', 'pull up', 'चिनअप', 'पुल']),
        'squat': any(word in query_lower for word in ['squat', 'स्क्वाट', 'बैठक']),
        'diet': any(word in query_lower for word in ['diet', 'food', 'nutrition', 'खाना', 'आहार']),
        'weight_loss': any(word in query_lower for word in ['weight loss', 'fat loss', 'reduce', 'वजन', 'मोटापा']),
        'muscle_gain': any(word in query_lower for word in ['muscle', 'gain', 'build', 'size', 'मांसपेशी', 'बनाना']),
        'cardio': any(word in query_lower for word in ['cardio', 'running', 'cycling', 'हृदय']),
        'form': any(word in query_lower for word in ['form', 'technique', 'सही', 'तरीका']),
        'program': any(word in query_lower for word in ['program', 'plan', 'routine', 'योजना', 'कार्यक्रम'])
    }
    
    # Return first matching intent
    for intent, matches in intent_map.items():
        if matches:
            return intent
    
    return 'general'