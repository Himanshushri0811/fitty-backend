
import os
import django
import sys
from pathlib import Path

# Setup Django Environment dynamically
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from diet.models import FoodItem

print("Seeding PRODUCT-LEVEL Intelligent Food Database...")

# Delete old data
# FoodItem.objects.delete() # Avoiding delete for safety, create if not exists or update.

intelligent_foods = [
    # --- BREAKFAST (High Energy, Fiber, Protein) ---
    {
        "name": "Oats Upma with Veggies",
        "calories": 280, "protein": 10, "carbs": 45, "fats": 6, "fiber": 8,
        "serving_unit": "1 bowl", "type": "Veg", "cuisine": "South Indian",
        "budget": "Low",
        "goal_tags": ["Fat Loss", "Energy"],
        "benefits": ["Sustained Energy", "High Fiber", "Heart Healthy"],
        "description": "Slow-digesting oats keep you full for hours. Perfect for fat loss.",
        "best_time": ["Breakfast"], "prep_time": 15, "cooking_difficulty": "Easy",
        "tags": ["breakfast", "fiber", "indian"]
    },
    {
        "name": "Paneer Paratha (Low Oil)",
        "calories": 350, "protein": 18, "carbs": 38, "fats": 14, "fiber": 4,
        "serving_unit": "1 medium", "type": "Veg", "cuisine": "North Indian",
        "budget": "Medium",
        "goal_tags": ["Muscle Gain", "Maintenance"],
        "benefits": ["High Protein", "Calcium Boost", "Satisfying"],
        "description": "A protein-packed start mostly from casein, great for muscle repair.",
        "best_time": ["Breakfast", "Lunch"], "prep_time": 20, "cooking_difficulty": "Medium",
        "tags": ["breakfast", "protein"]
    },
    {
        "name": "Masala Omelette (3 Eggs)",
        "calories": 240, "protein": 19, "carbs": 3, "fats": 16, "fiber": 1,
        "serving_unit": "3 egg omelette", "type": "Egg", "cuisine": "Global",
        "budget": "Low",
        "goal_tags": ["Fat Loss", "Muscle Gain", "Keto"],
        "benefits": ["Complete Protein", "Brain Health", "Zero Carbs"],
        "description": "The gold standard for bioavailability. Keeps insulin low.",
        "best_time": ["Breakfast", "Dinner"], "prep_time": 10, "cooking_difficulty": "Easy",
        "tags": ["keto", "high-protein"]
    },

    # --- LUNCH (Balanced Macros) ---
    {
        "name": "Rajma Chawal (Brown Rice)",
        "calories": 420, "protein": 16, "carbs": 70, "fats": 8, "fiber": 14,
        "serving_unit": "1 bowl", "type": "Veg", "cuisine": "North Indian",
        "budget": "Low",
        "goal_tags": ["Maintenance", "Energy"],
        "benefits": ["Complete Amino Profile", "Iron Rich", "Comfort Food"],
        "description": "When paired with rice, kidney beans provide complete protein.",
        "best_time": ["Lunch"], "prep_time": 45, "cooking_difficulty": "Medium",
        "tags": ["lunch", "staple"]
    },
    {
        "name": "Grilled Chicken Salad",
        "calories": 320, "protein": 40, "carbs": 10, "fats": 12, "fiber": 6,
        "serving_unit": "1 large bowl", "type": "Non-Veg", "cuisine": "Continental",
        "budget": "Medium",
        "goal_tags": ["Fat Loss", "Muscle Gain"],
        "benefits": ["Lean Muscle", "Micronutrients", "Low Calorie"],
        "description": "Maximum protein with minimum calories. Ideal for cutting.",
        "best_time": ["Lunch", "Dinner"], "prep_time": 20, "cooking_difficulty": "Easy",
        "tags": ["clean-eating", "cutting"]
    },
    {
        "name": "Palak Paneer & Roti",
        "calories": 380, "protein": 20, "carbs": 30, "fats": 20, "fiber": 6,
        "serving_unit": "1 bowl + 2 roti", "type": "Veg", "cuisine": "North Indian",
        "budget": "Medium",
        "goal_tags": ["Muscle Gain", "Keto"],
        "benefits": ["Iron Rich", "Healthy Fats", "Vitamin K"],
        "description": "Spinach provides essential micros while Paneer drives protein.",
        "best_time": ["Lunch", "Dinner"], "prep_time": 30, "cooking_difficulty": "Medium",
        "tags": ["iron", "vitamin-rich"]
    },

    # --- DINNER (Light & Recovery) ---
    {
        "name": "Moong Dal Khichdi",
        "calories": 300, "protein": 14, "carbs": 50, "fats": 5, "fiber": 8,
        "serving_unit": "1 bowl", "type": "Veg", "cuisine": "Indian",
        "budget": "Low",
        "goal_tags": ["Fat Loss", "Maintenance"],
        "benefits": ["Gut Healing", "Easy Digestion", "Light"],
        "description": "The ultimate light dinner. Easy on the stomach before sleep.",
        "best_time": ["Dinner"], "prep_time": 25, "cooking_difficulty": "Easy",
        "tags": ["light", "gut-health"]
    },
    {
        "name": "Grilled Fish with Veggies",
        "calories": 280, "protein": 35, "carbs": 8, "fats": 10, "fiber": 5,
        "serving_unit": "1 fillet", "type": "Non-Veg", "cuisine": "Global",
        "budget": "High",
        "goal_tags": ["Muscle Gain", "Fat Loss"],
        "benefits": ["Omega-3s", "Fast Recovery", "Lean Protein"],
        "description": "Omega-3s support joint health and reduce inflammation.",
        "best_time": ["Dinner", "Lunch"], "prep_time": 20, "cooking_difficulty": "Medium",
        "tags": ["omega3", "premium"]
    },
    
    # --- SNACKS (Smart Craving Killers) ---
    {
        "name": "Roasted Chana & Peanuts",
        "calories": 180, "protein": 9, "carbs": 18, "fats": 8, "fiber": 5,
        "serving_unit": "1 handful", "type": "Veg", "cuisine": "Indian",
        "budget": "Low",
        "goal_tags": ["Fat Loss", "Maintenance"],
        "benefits": ["Crunchy Satisfaction", "Satiety"],
        "description": "Cheap, effective, and stops junk cravings.",
        "best_time": ["Snack"], "prep_time": 5, "cooking_difficulty": "Easy",
        "tags": ["snack", "cheap"]
    },
    {
        "name": "Greek Yogurt Bowl",
        "calories": 150, "protein": 15, "carbs": 10, "fats": 5, "fiber": 2,
        "serving_unit": "1 cup", "type": "Veg", "cuisine": "Global",
        "budget": "High",
        "goal_tags": ["Muscle Gain", "Fat Loss"],
        "benefits": ["Probiotics", "Slow Carbs"],
        "description": "Casein protein feeds muscles while you sleep (if eaten late).",
        "best_time": ["Snack", "Breakfast"], "prep_time": 5, "cooking_difficulty": "Easy",
        "tags": ["probiotic", "calcium"]
    },
]

count = 0
for f in intelligent_foods:
    # Update or Create logic using name as key
    existing = FoodItem.objects(name=f['name']).first()
    if existing:
        # Update fields
        for key, value in f.items():
            setattr(existing, key, value)
        existing.save()
        print(f"🔄 Updated {f['name']}")
    else:
        FoodItem(**f).save()
        print(f"✅ Created {f['name']}")
    count += 1

print(f"Done! Seeded {count} intelligent foods.")
