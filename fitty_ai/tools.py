import os
from django.conf import settings
from langchain.tools import tool
from accounts.models import User
from workouts.models import WorkoutPlan, Exercise

@tool
def get_user_profile(user_id: str):
    """(DEPRECATED) Profile is now automatically injected into context."""
    return "Profile is already in your SYSTEM PROMPT CONTEXT. DO NOT CALL THIS TOOL."

@tool
def workout_generator(goal: str, fitness_level: str = "Beginner"):
    """Creates workout plans based on user goals and fitness level."""
    return f"Based on {goal} and {fitness_level} level, I recommend 3 days of Full Body strength training with 2 days of Cardio. Focus on compound movements."

@tool
def diet_generator(weight: float, goal: str):
    """Calculates calories and provides a structured Indian meal plan based on user goals."""
    try:
        weight = float(weight)
        base_calories = weight * 30
        if "loss" in goal.lower():
            target = base_calories - 500
            plan_type = "Fat Loss Diet"
            breakfast = "2 Besan Chilla with Mint Chutney"
            lunch = "1 Katori Dal, 1 Roti, Sabzi and Salad"
            dinner = "Grilled Paneer/Chicken Tikka with clear soup"
        elif "gain" in goal.lower():
            target = base_calories + 500
            plan_type = "Muscle Gain Diet"
            breakfast = "Oats with Milk, Banana, Peanut Butter and 4 Egg Whites"
            lunch = "2 Katori Dal/Chicken Curry, 3 Rotis, Rice, Curd"
            dinner = "Paneer Bhurji / Chicken breast, 2 Rotis, mixed Salad"
        else:
            target = base_calories
            plan_type = "Maintenance Diet"
            breakfast = "2 Poha / Upma bowls with peanuts"
            lunch = "Normal Ghar Ka Khana (Dal, Roti, Sabzi, Dahi)"
            dinner = "Light Dal Khichdi or Grilled Soya Chunks"
            
        return f"[{plan_type} - Target: {int(target)} kcal]\nBreakfast: {breakfast}\nLunch: {lunch}\nDinner: {dinner}"
    except Exception as e:
        return f"Error calculating diet: {str(e)}"

@tool
def exercise_explainer(exercise_name: str):
    """Explains how to perform a specific exercise."""
    try:
        ex = Exercise.objects(name__icontains=exercise_name).first()
        if ex:
            return f"{ex.name}: {ex.description}. Form focus: {ex.target_muscle_group}."
        return f"I couldn't find details for {exercise_name}, but usually, focus on slow controlled movements and breathing."
    except Exception as e:
        return f"Error explaining exercise: {str(e)}"

@tool
def motivation_generator():
    """Provides supportive fitness motivation."""
    import random
    quotes = [
        "Consistency is key! Every rep counts.",
        "You're doing great, keep pushing your limits.",
        "Strength doesn't come from what you can do. It comes from overcoming the things you once thought you couldn't."
    ]
    return random.choice(quotes)

@tool
def generate_plan_pdf(title: str, content: str):
    """Generates a structured PDF for a user's diet or workout plan when explicitly requested. The 'content' should be a detailed string with newlines. Returns a downloadable link."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        media_dir = os.path.join(settings.BASE_DIR, 'media', 'pdfs')
        os.makedirs(media_dir, exist_ok=True)
        filename = f"{title.replace(' ', '_')}.pdf"
        filepath = os.path.join(media_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, title.upper())
        c.setFont("Helvetica", 12)
        
        y = 710
        lines = content.split('\\n') if '\\n' in content else content.split('\n')
        for line in lines:
            if y < 50:
                c.showPage()
                y = 750
            if len(line.strip()) > 0:
                # Basic wrapping
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) < 75:
                        current_line += word + " "
                    else:
                        c.drawString(100, y, current_line)
                        y -= 20
                        current_line = word + " "
                if current_line:
                    c.drawString(100, y, current_line)
                    y -= 20
            else:
                y -= 20 # blank line
                
        c.save()
        return f"/media/pdfs/{filename}"
    except Exception as e:
        return f"Error creating PDF: {str(e)}"
