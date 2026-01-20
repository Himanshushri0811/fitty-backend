import uuid
import random

def generate_daily_plan(user, date_str):
    """
    Generates a daily plan for the user based on a simple logic (can be AI-enhanced later).
    """
    
    # Pool of activities
    workouts = [
        {"title": "Morning Yoga Flow", "type": "yoga", "time": "07:00 AM", "note": "Focus on breathing."},
        {"title": "HIIT Cardio Blast", "type": "workout", "time": "08:00 AM", "note": "Keep your heart rate up!"},
        {"title": "Upper Body Strength", "type": "workout", "time": "06:00 PM", "note": "Push your limits safely."},
        {"title": "Evening Stretch", "type": "recovery", "time": "09:00 PM", "note": "Relax your muscles."}
    ]
    
    meals = [
        {"title": "High Protein Breakfast", "type": "diet", "time": "09:00 AM", "note": "Eggs or Tofu scramble."},
        {"title": "Green Smoothie", "type": "diet", "time": "11:00 AM", "note": "Spinach, banana, and protein."},
        {"title": "Lean Chicken/Paneer Salad", "type": "diet", "time": "01:00 PM", "note": "Light and nutritious."},
        {"title": "Nuts & Hydration", "type": "diet", "time": "04:00 PM", "note": "Handful of almonds + water."}
    ]
    
    items_data = []
    
    # Pick 1 Morning activity
    morning = random.choice(workouts[:2])
    items_data.append(morning)
    
    # Pick 1 Afternoon/Lunch activity
    lunch = random.choice(meals)
    items_data.append(lunch)
    
    # Pick 1 Evening activity
    evening = random.choice(workouts[2:])
    items_data.append(evening)
    
    # Convert to PlanItem structure
    from .models import PlanItem
    
    items = []
    for data in items_data:
        items.append(PlanItem(
            id=str(uuid.uuid4()),
            title=data['title'],
            time=data['time'],
            type=data['type'],
            status='pending',
            coach_note=data['note']
        ))
        
    # Coach Message
    coach_messages = [
        f"Hey {user.username}, let's crush today's goals!",
        "Consistency is key. You've got this!",
        "Remember to drink water between these sessions.",
        "A fresh day for a fresh start. Let's go!",
        "Stay focused and trust the process."
    ]
    
    return items, random.choice(coach_messages)
