import google.generativeai as genai
import json
import os
from django.conf import settings

# Configure API (Reuse existing setup)
api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, 'GEMINI_API_KEY', None)
if api_key:
    genai.configure(api_key=api_key)

from ai.services.model_selector import get_best_gemini_model

def generate_food_persona(food_name, user_name, nutrient_summary=""):
    """
    Generates a Hinglish persona for a food item.
    """
    if not api_key:
        return {
            "persona_text": f"Hello {user_name}, I am {food_name}. Please check my benefits!",
            "benefits": ["Healthy", "Nutritious"],
            "fitness_relevance": "Good for health"
        }

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
    
    try:
        model_name = get_best_gemini_model()
        model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini Food Gen Error: {e}")
        return {
             "persona_text": f"Namaste {user_name}, main {food_name} hoon. Connection error, but I am still healthy!",
             "benefits": ["High Nutrition", "Natural"],
             "fitness_relevance": "Good for general fitness"
        }

def calculate_macros_from_text(food_text):
    """
    Parses natural language food text (e.g., "2 roti and dal") and estimates macros.
    """
    if not api_key:
        return {"calories": 0, "protein": 0, "carbs": 0, "fats": 0, "items": []}

    prompt = f"""
    Analyze the following food log and calculate total approximate nutrition.
    Food Log: "{food_text}"

    Context: Indian Home Cooked Food usually.
    
    Task:
    1. Identify items and quantities.
    2. Estimate Calories, Protein(g), Carbs(g), Fats(g).
    3. Sum them up.

    Output JSON ONLY:
    {{
        "items": ["list", "of", "detected", "items"],
        "total_calories": 0,
        "total_protein": 0,
        "total_carbs": 0,
        "total_fats": 0
    }}
    """
    
    try:
        model_name = get_best_gemini_model()
        model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini Macro Calc Error: {e}")
        return {"error": "Failed to calculate macros"}

def generate_food_deep_dive(food_name):
    """
    Generates detailed research content for a food (Simulating a Google Search).
    """
    if not api_key:
        return {"description": "API Key Missing", "recipes": [], "history": ""}

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
    
    try:
        model_name = get_best_gemini_model()
        model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini Deep Dive Error: {e}")
        return {"error": "Failed to research"}
