
import google.generativeai as genai
from django.conf import settings
import os

def get_gemini_response(prompt):
    """
    Get response from Gemini Flash model
    """
    try:
        api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY'))
        if not api_key:
            return "AI Configuration Missing (API Key)"
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "I am currently unable to connect to the AI brain. However, this workout is scientifically structured for your goals."

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