import os
import json
import requests
from google import genai
from django.conf import settings
from ai.services.model_selector import get_best_gemini_model

# --- API KEYS ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or getattr(settings, 'GEMINI_API_KEY', None)
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or getattr(settings, 'GROQ_API_KEY', None)

# --- HELPER: ROBUST GENERATION ---
def generate_robust_json(prompt, error_context="Generation"):
    """
    Tries Gemini first (updated SDK), then falls back to Groq Llama3.
    """
    
    # 1. Try Groq (PRIORITY due to previous Gemini instability)
    if GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a JSON-only API. Return valid JSON only. No markdown."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }
            resp = requests.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                return json.loads(content)
        except Exception:
            pass

    # 2. Try Gemini (Fallback - New SDK)
    if GEMINI_API_KEY:
        try:
            model_name = get_best_gemini_model()
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"⚠️ Gemini Failed in {error_context}: {e}")

    return None

# --- PUBLIC FUNCTIONS ---

def generate_food_persona(food_name, user_name, nutrient_summary=""):
    """
    Generates a Hinglish persona for a food item.
    """
    prompt = f"""
    You are a fitness nutrition expert. 
    Role: You ARE the food item itself ({food_name}).
    User: {user_name}
    Nutrients: {nutrient_summary}

    Goal: Speak to the user in first person ("Hello {user_name}, main {food_name} hoon...").
    Language: Hinglish (Hindi + English mix).
    Tone: Friendly, energetic, fitness-focused.

    Requirements:
    1. Greeting: Personalized greeting.
    2. Intro: Short intro about yourself.
    3. Fitness Relevance: Why should they eat you? (Muscle gain/weight loss context).
    4. Format: Valid JSON ONLY. No markdown.

    Output format:
    {{
        "persona_text": "Full spoken text here...",
        "benefits": ["Short benefit 1", "Short benefit 2"],
        "fitness_relevance": "One line summary of why I fit in your diet."
    }}
    """
    
    data = generate_robust_json(prompt, "Food Persona")
    
    if data:
        return data
    
    # Fallback Data
    return {
            "persona_text": f"Namaste {user_name}, main {food_name} hoon. I am offline but healthy!",
            "benefits": ["High Nutrition", "Natural"],
            "fitness_relevance": "Good for general fitness"
    }

def calculate_macros_from_text(food_text):
    """
    Parses natural language food text (e.g., "2 roti and dal") and estimates macros.
    """
    prompt = f"""
    Analyze the following food log and calculate total approximate nutrition.
    Food Log: "{food_text}"

    Context: Indian Home Cooked Food usually.
    
    Task:
    1. Identify items and quantities.
    2. Estimate Calories, Protein(g), Carbs(g), Fats(g).
    3. Sum them up to get 'total_calories', 'total_protein', etc.

    Output JSON ONLY:
    {{
        "items": ["list", "of", "detected", "items"],
        "total_calories": 0,
        "total_protein": 0,
        "total_carbs": 0,
        "total_fats": 0
    }}
    """
    
    data = generate_robust_json(prompt, "Macro Calc")
    
    if data:
        return data

    return {"error": "Failed to calculate macros. AI services unavailable."}

def generate_food_deep_dive(food_name):
    """
    Generates detailed research content for a food (Simulating a Google Search).
    """
    prompt = f"""
    Research detailed information about: "{food_name}".
    Role: You are a food historian and chef.

    Output JSON ONLY:
    {{
        "long_description": "Detailed 2-3 paragraph description about origin, taste profile, and global usage.",
        "health_benefits_detailed": ["Detailed benefit 1", "Detailed benefit 2", "Detailed benefit 3"],
        "best_time_to_eat": "Morning/Night etc with reason",
        "who_should_avoid": "Diabetics/etc with reason",
        "recipes": [
            {{ "name": "Recipe 1", "steps": ["Step 1", "Step 2"] }},
            {{ "name": "Recipe 2", "steps": ["Step 1", "Step 2"] }}
        ],
        "fun_fact": "A surprising fact"
    }}
    """
    
    data = generate_robust_json(prompt, "Deep Dive")
    if data: 
        return data
        
    return {"description": "Research unavailable offline.", "recipes": [], "history": ""}
