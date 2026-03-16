import os
from google import genai
from django.conf import settings

def generate_fitty_response(user_message):
    """
    Generate a response from Fitty AI using the new Google GenAI SDK.
    Model: gemini-2.0-flash
    """
    try:
        # 1. Get API Key from settings or environment
        api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY'))
        if not api_key:
            return "❌ Fitty is having trouble connecting: API Key missing."

        # 2. Initialize the client using the new SDK
        client = genai.Client(api_key=api_key)

        # 3. Generate response using gemini-2.0-flash
        # This model is faster and supports the latest features without 404/v1beta issues
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_message,
        )

        return response.text

    except Exception as e:
        print(f"🔴 Fitty AI Error (utils.py): {str(e)}")
        # Friendly error message for users
        return "I'm having a small brain freeze right now, Champ. Let's try that again in a second! Keep the energy up!"

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