import google.generativeai as genai
import json
import os
from django.conf import settings
from diet.models import FoodItem

# Configure API (Reuse existing setup)
api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, 'GEMINI_API_KEY', None)
if api_key:
    genai.configure(api_key=api_key)

from ai.services.model_selector import get_best_gemini_model

def discover_new_foods(goal, diet_type):
    """
    Asks Gemini to suggest unique foods based on the user's goal and diet.
    Returns a list of food objects (dicts).
    """
    MODEL_NAME = get_best_gemini_model()
    if not api_key:
        print("Skipping AI Discovery: No API Key")
        return []

    print(f"🤖 AI Discovery: Searching for {diet_type} foods for {goal}...")
    
    prompt = f"""
    You are a professional nutritionist.
    Task: Suggest 5 UNIQUE and LESS COMMON Indian/Global foods suitable for:
    - Goal: {goal}
    - Diet Type: {diet_type}
    
    Requirements:
    1. Foods must be real, specific dishes (e.g., "Quinoa Salad", "Soya Chunk Curry").
    2. Avoid generic names like "Oats" or "Eggs". Be specific.
    3. Output JSON ONLY.
    
    Output Format:
    [
        {{
            "name": "Food Name",
            "calories": 0,
            "protein": 0.0,
            "carbs": 0.0,
            "fats": 0.0,
            "serving_unit": "1 bowl",
            "benefits": ["Benefit 1", "Benefit 2"],
            "fitness_relevance": "Why it fits the goal",
            "best_time": ["Breakfast", "Lunch"]
        }}
    ]
    """
    
    try:
        model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        foods = json.loads(response.text)
        
        saved_count = 0
        for f in foods:
            # Check duplicate
            if not FoodItem.objects(name__iexact=f['name']).first():
                # Use a reliable placeholder or simple image service for now
                # Unsplash source API is deprecated/unreliable without key
                # We use a nice text placeholder that looks like a UI element
                
                safe_name = f['name'].replace(' ', '+')
                image_url = f"https://placehold.co/600x400/2a2a35/FFF?text={safe_name}"
                
                FoodItem(
                    name=f['name'],
                    calories=f['calories'],
                    protein=f['protein'],
                    carbs=f['carbs'],
                    fats=f['fats'],
                    serving_unit=f.get('serving_unit', '1 serving'),
                    benefits=f.get('benefits', []),
                    fitness_relevance=f.get('fitness_relevance', ''),
                    type=diet_type, 
                    # Default tags
                    goal_tags=[goal],
                    image_url=image_url
                ).save()
                saved_count += 1
                
        print(f"✅ AI Discovered & Saved {saved_count} new foods.")
        return foods # Return just to confirm success, though we fetched from DB mostly
        
    except Exception as e:
        print(f"Gemini Discovery Error: {e}")
        return []
