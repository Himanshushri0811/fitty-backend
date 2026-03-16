from langchain.tools import tool
from accounts.models import User
from workouts.models import WorkoutPlan, Exercise
# from ai.services.food_generator import generate_diet_plan  # Removed as it's unused and causing ImportError

@tool
def get_user_profile(user_id: str):
    """Fetches user data such as weight, goal, activity level, and gender."""
    try:
        user = User.objects.get(id=user_id)
        return {
            "name": user.name,
            "weight": user.weight,
            "goal": user.goal,
            "activity_level": user.activity_level,
            "gender": user.gender,
            "fitness_level": user.fitness_level,
            "target_weight": user.target_weight
        }
    except Exception as e:
        return f"Error fetching profile: {str(e)}"

@tool
def workout_generator(user_id: str, goal: str):
    """Creates workout plans based on user goals and current profile."""
    # In a real scenario, this might call another LLM or a predefined logic.
    # For now, we fetch the active plan or suggest a simple structure.
    try:
        active_plan = WorkoutPlan.objects(user_id=user_id, is_active=True).first()
        if active_plan:
            return f"Current Plan: {active_plan.name}. Goal: {active_plan.goal}. Focus areas: {[r.focus_area for r in active_plan.routines]}"
        return f"No active plan found. For {goal}, I recommend 3 days of Full Body strength training with 2 days of Cardio."
    except Exception as e:
        return f"Error generating workout: {str(e)}"

@tool
def diet_generator(user_id: str):
    """Calculates calories and protein targets based on user weight and goal."""
    try:
        user = User.objects.get(id=user_id)
        weight = user.weight or 70
        goal = user.goal or "Maintenance"
        
        # Simple heuristic
        base_calories = weight * 30
        if "loss" in goal.lower():
            target = base_calories - 500
            protein = weight * 2
        elif "gain" in goal.lower():
            target = base_calories + 500
            protein = weight * 1.8
        else:
            target = base_calories
            protein = weight * 1.5
            
        return f"Target: {target} kcal. Protein: {protein}g per day."
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
        "Strength doesn't come from what you can do. It comes from overcoming the things you once thought you couldn't.",
        "Your future self will thank you for today's workout."
    ]
    return random.choice(quotes)
