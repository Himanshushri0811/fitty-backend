from random import choice
from .models import DietPlan, DailyMealSlot, MealItem, FoodItem, DietProfile

def calculate_target_calories(user, goal):
    """
    Revised calorie calculator using Mifflin-St Jeor (Approx)
    """
    # Assuming user model might have weight/height in future. 
    # For now, using standard baselines modified by goal.
    base = 2200 if user.gender == 'Male' else 1800
    
    if goal == 'Weight Loss':
        return base - 400
    elif goal == 'Muscle Gain':
        return base + 300
    return base

def get_or_create_weekly_plan(user):
    """
    Generates a smart plan based on Goal + Budget + Diet Type
    """
    active_plan = DietPlan.objects(user=user, is_active=True).first()
    if active_plan:
        return active_plan

    # GENERATE NEW PLAN
    return generate_new_plan(user)

def generate_new_plan(user):
    profile = DietProfile.objects(user=user).first()
    if not profile:
        return None
        
    # Deactivate any existing active plans to be safe
    DietPlan.objects(user=user, is_active=True).update(set__is_active=False)
        
    # 1. Filter by Diet Type
    allowed_types = [profile.diet_type]
    if profile.diet_type == 'Non-Veg':
        allowed_types = ['Veg', 'Non-Veg', 'Egg', 'Vegan']
    elif profile.diet_type == 'Egg':
        allowed_types = ['Veg', 'Egg', 'Vegan']
    elif profile.diet_type == 'Veg':
        allowed_types = ['Veg', 'Vegan']
    
    base_query = FoodItem.objects(type__in=allowed_types)
    
    # 2. Filter / Prioritize by Budget (Strictness: Soft)
    # If user wants Low Budget, we prefer Low.
    # If High, we allow everything but prioritize High/Medium for variety.
    
    # 3. Filter by Goal (Strictness: Soft)
    # If Weight Loss, avoid high carb/fat items if possible? 
    # Actually, relying on `good_for` tag is better.
    
    # Let's fetch compatible foods
    all_foods = list(base_query)
    
    # Scoring Function to pick best foods
    def score_food(food):
        score = 0
        
        # Budget Match
        if profile.budget_level == 'Low':
            if food.budget == 'Low': score += 10
            elif food.budget == 'Medium': score += 5
            else: score -= 5 # Penalize expensive
        elif profile.budget_level == 'Medium':
            if food.budget == 'Medium': score += 10
            elif food.budget == 'Low': score += 8
        else: # High
            score += 5 # Everything is good
            
        # Goal Match
        if hasattr(food, 'goal_tags') and profile.goal in food.goal_tags:
            score += 15
            
        return score

    # Sort foods by score
    all_foods.sort(key=score_food, reverse=True)
    
    # Take top 50% as candidates to ensure quality but keep some variety
    if not all_foods: return None
    candidates = all_foods[:max(5, len(all_foods)//2)] + all_foods # Mix top with some randoms for variety
    
    # Helper to pick
    def pick_food(time_slot=None):
        # Filter candidates by Time Slot
        subset = candidates
        if time_slot:
           # Check if food.best_time contains the slot (case insensitive check usually needed but we enforce Title Case)
           time_matched = [f for f in candidates if time_slot in (f.best_time or [])]
           if time_matched: 
               subset = time_matched
           # If no exact time match, fallback to subset (or risky fallback)
           
        return choice(subset) if subset else choice(all_foods)

    # Helper to make a day
    def make_day():
        slots = []
        # Breakfast
        bf_food = pick_food("Breakfast")
        slots.append(DailyMealSlot(name="Breakfast", items=[MealItem(food_item=bf_food, quantity=1, calories_snapshot=bf_food.calories)], time="08:00 AM"))
        
        # Lunch
        lunch_food = pick_food("Lunch")
        slots.append(DailyMealSlot(name="Lunch", items=[MealItem(food_item=lunch_food, quantity=1, calories_snapshot=lunch_food.calories)], time="01:00 PM"))
        
        # Dinner (Lighter?)
        dinner_food = pick_food("Dinner")
        slots.append(DailyMealSlot(name="Dinner", items=[MealItem(food_item=dinner_food, quantity=1, calories_snapshot=dinner_food.calories)], time="08:00 PM"))
        
        # Snack
        snack_food = pick_food("Snack")
        slots.append(DailyMealSlot(name="Snack", items=[MealItem(food_item=snack_food, quantity=1, calories_snapshot=snack_food.calories)], time="05:00 PM"))
        
        return slots

    plan = DietPlan(
        user=user,
        monday=make_day(),
        tuesday=make_day(),
        wednesday=make_day(),
        thursday=make_day(),
        friday=make_day(),
        saturday=make_day(),
        sunday=make_day()
    )
    plan.save()
    return plan
