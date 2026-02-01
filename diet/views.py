from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
import random

from .models import DietProfile, FoodItem, DietPlan, MealItem
from .serializers import DietProfileSerializer, FoodItemSerializer, DietPlanSerializer
from .utils import calculate_target_calories, get_or_create_weekly_plan

# Lazy Import to avoid circular dependencies if any
def get_ai_generator():
    from ai.services.food_generator import generate_food_persona
    return generate_food_persona

class DietProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = DietProfile.objects(user=request.user).first()
        if not profile:
            return Response({"message": "Profile not setup"}, status=404)
        
        serializer = DietProfileSerializer(profile)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        profile = DietProfile.objects(user=request.user).first()
        
        if 'target_calories' not in data or not data['target_calories']:
            cal_target = calculate_target_calories(request.user, data.get('goal', 'Maintenance'))
            data['target_calories'] = cal_target

        if profile:
            serializer = DietProfileSerializer(profile, data=data, partial=True)
        else:
            serializer = DietProfileSerializer(data=data)
        
        if serializer.is_valid():
            if not profile:
                profile = serializer.save(user=request.user)
                get_or_create_weekly_plan(request.user) # First time
            else:
                serializer.save()
                # If profile updated, we should ideally refresh the plan to match new goal/budget
                # But to avoid losing progress, maybe we make this optional? 
                # For now, let's FORCE it for the "Smart" experience.
                from .utils import generate_new_plan
                generate_new_plan(request.user)
                
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class WeeklyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plan = get_or_create_weekly_plan(request.user)
        if not plan:
            return Response({"message": "Could not generate plan. Please ensure profile is set and foods exist."}, status=400)
        serializer = DietPlanSerializer(plan)
        
        # Fetch targets from profile
        profile = DietProfile.objects(user=request.user).first()
        target_calories = profile.target_calories if profile else 2000
        # Estimate Protein target (approx 30% of calories)
        target_protein = int((target_calories * 0.3) / 4)
        
        return Response({
            "plan": serializer.data,
            "targets": {
                "calories": target_calories,
                "protein": target_protein
            }
        })

class FoodSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
        foods = FoodItem.objects(name__icontains=query).limit(10)
        serializer = FoodItemSerializer(foods, many=True)
        return Response(serializer.data)

class ReplaceMealView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        day = request.data.get('day', '').lower()
        period = request.data.get('period')
        index = int(request.data.get('index', 0))
        food_id = request.data.get('food_id') # If manual selection
        smart_option = request.data.get('replace_mode') # 'similar', 'high_protein', 'budget', 'fast'

        plan = DietPlan.objects(user=request.user, is_active=True).first()
        if not plan: return Response({"error": "No active plan"}, 404)
        if not hasattr(plan, day): return Response({"error": "Invalid day"}, 400)

        day_slots = getattr(plan, day)
        target_slot = next((slot for slot in day_slots if slot.name == period), None)
        if not target_slot: return Response({"error": "Meal slot not found"}, 404)
        if index < 0 or index >= len(target_slot.items): return Response({"error": "Item index out of bounds"}, 400)
        
        current_meal = target_slot.items[index]
        current_cals = current_meal.calories_snapshot
        
        food = None
        reason = "Manual replacement."

        if food_id:
            food = FoodItem.objects(id=food_id).first()
        elif smart_option:
            # AUTO-FIND LOGIC based on Context
            try:
                current_food_id = current_meal.food_item.id if current_meal.food_item else None
            except Exception: # Handle broken references (DoesNotExist)
                current_food_id = None
            
            # Base query: Exclude current food, match slot, match diet type
            profile = DietProfile.objects(user=request.user).first()
            allowed_types = [profile.diet_type]
            if profile.diet_type == 'Non-Veg': allowed_types += ['Veg', 'Egg']
            
            query = FoodItem.objects(type__in=allowed_types, id__ne=current_food_id)
            # Filter by slot (must be suitable for period e.g. Breakfast)
            # We filter in python for flexibility or complex list match
            candidates = [f for f in query if period in (f.best_time or [])]
            if not candidates: candidates = list(query) # Fallback

            if smart_option == 'high_protein':
                # Sort by Protein desc
                candidates.sort(key=lambda x: x.protein, reverse=True)
                food = candidates[0] if candidates else None
                reason = f"Switched to {food.name} for higher protein ({food.protein}g) to support muscle repair."
            
            elif smart_option == 'budget':
                # Prefer Low > Medium > High
                budget_map = {'Low': 3, 'Medium': 2, 'High': 1}
                candidates.sort(key=lambda x: budget_map.get(x.budget, 0), reverse=True)
                food = candidates[0] if candidates else None
                reason = f"Switched to a wallet-friendly option ({food.budget} Budget)."
            
            elif smart_option == 'fast':
                 # Sort by Prep Time
                candidates.sort(key=lambda x: x.prep_time)
                food = candidates[0] if candidates else None
                reason = f"Quick fix! {food.name} takes only {food.prep_time} mins to prep."
            
            else: # 'similar' or default
                # Find closest calories
                candidates.sort(key=lambda x: abs(x.calories - current_cals))
                food = candidates[0] if candidates else None
                reason = f"Replaced with {food.name} as a calorie-matched alternative."

        if not food:
            return Response({"error": "Food not found or no smart match"}, 404)

        new_meal_item = MealItem(
            food_item=food,
            quantity=1, 
            calories_snapshot=food.calories,
            custom_name=None
        )
        
        target_slot.items[index] = new_meal_item
        plan.save()
        
        return Response({
            "message": "Meal updated successfully", 
            "new_food": food.name,
            "reason": reason
        })

class SeedFoodView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        foods = [
            {"name": "Oats Upma", "calories": 250, "serving_unit": "1 bowl", "type": "Veg", "protein": 8, "carbs": 40, "fats": 5, "cuisine": "Indian"},
            {"name": "Poha", "calories": 270, "serving_unit": "1 plate", "type": "Veg", "protein": 5, "carbs": 50, "fats": 7, "cuisine": "Indian"},
            {"name": "Paneer Bhurji", "calories": 300, "serving_unit": "150g", "type": "Veg", "protein": 18, "carbs": 5, "fats": 22, "cuisine": "Indian"},
            {"name": "Dal Tadka", "calories": 180, "serving_unit": "1 bowl", "type": "Veg", "protein": 10, "carbs": 25, "fats": 6, "cuisine": "Indian"},
            {"name": "Chicken Curry", "calories": 350, "serving_unit": "1 bowl", "type": "Non-Veg", "protein": 30, "carbs": 10, "fats": 15, "cuisine": "Indian"},
            {"name": "Grilled Fish", "calories": 220, "serving_unit": "1 fillet", "type": "Non-Veg", "protein": 25, "carbs": 0, "fats": 10, "cuisine": "Global"},
            {"name": "Roti", "calories": 100, "serving_unit": "1 piece", "type": "Veg", "protein": 3, "carbs": 20, "fats": 1, "cuisine": "Indian"},
            {"name": "Brown Rice", "calories": 210, "serving_unit": "1 cup cooked", "type": "Veg", "protein": 5, "carbs": 44, "fats": 2, "cuisine": "Global"},
            {"name": "Boiled Eggs", "calories": 140, "serving_unit": "2 large", "type": "Egg", "protein": 12, "carbs": 1, "fats": 10, "cuisine": "Global"},
        ]
        
        count = 0
        for f in foods:
            if not FoodItem.objects(name=f['name']).first():
                FoodItem(**f).save()
                count += 1
                
        return Response({"message": f"Seeded {count} foods"})

# ---------------------------------------------------
# NEW: AI SMART BOX VIEW
# ---------------------------------------------------

class DietCarouselView(APIView):
    """
    Returns foods for the AI Smart Box. 
    Triggers AI Generation if content is missing.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_name = request.user.name or "Friend"
        
        # 0. Get User Context
        profile = DietProfile.objects(user=request.user).first()
        goal = profile.goal if profile else "Healthy"
        diet_type = profile.diet_type if profile else "Veg"

        # 1. Fetch foods suitable for the user (Goal + Diet)
        # We try to find foods that match the goal OR just general healthy ones
        
        # Count existing relevant foods
        # Filter Logic: Type matches AND (Goal matches OR generic)
        # MongoEngine doesn't support easy OR query with text search mixed, so we do simple filtering
        
        relevant_count = FoodItem.objects(type=diet_type).count()
        
        # DYNAMIC DISCOVERY: If we have very few foods, fetch from AI
        if relevant_count < 10:
             # Lazy import discovery
             from ai.services.food_discovery import discover_new_foods
             # Trigger explicitly (blocking for now, ideally background task)
             discover_new_foods(goal, diet_type)

        # 2. Get Random Sample
        pipeline = [
            {"$match": {"type": diet_type}}, 
            {"$sample": {"size": 5}}
        ]
        
        random_foods = list(FoodItem.objects.aggregate(*pipeline))
        
        results = []
        gen_func = get_ai_generator()
        user_name = request.user.name or "Friend"
        
        for food_data in random_foods:
            # Aggregate returns dict, not Document object.
            # We need to update if fields are missing.
            # Convert to ID to fetch Document for saving.
            f_id = food_data['_id']
            # We should refetch as Document to save updates easily
            food_doc = FoodItem.objects(id=f_id).first()
            if not food_doc: continue
            
            # Check if AI content exists
            if not food_doc.ai_persona_text:
                # Generate!
                nutrient_summary = f"{food_doc.calories} cal, {food_doc.protein}g protein"
                ai_content = gen_func(food_doc.name, user_name, nutrient_summary)
                
                food_doc.ai_persona_text = ai_content.get("persona_text", "")
                food_doc.benefits = ai_content.get("benefits", [])
                food_doc.fitness_relevance = ai_content.get("fitness_relevance", "")
                # Default image if empty (Use a placeholder service or Unsplash if we had logic)
                if not food_doc.image_url:
                     # Simple logic: generated placeholder with text
                     food_doc.image_url = f"https://placehold.co/400x300?text={food_doc.name.replace(' ', '+')}"
                
                food_doc.save()
            
            # Build Response
            results.append({
                "id": str(food_doc.id),
                "name": food_doc.name,
                "image_url": food_doc.image_url,
                "persona_text": food_doc.ai_persona_text,
                "fitness_relevance": food_doc.fitness_relevance,
                "benefits": food_doc.benefits,
                "macros": {
                    "calories": food_doc.calories,
                    "protein": food_doc.protein,
                    "carbs": food_doc.carbs,
                    "fats": food_doc.fats
                }
            })
            
        return Response(results)

class DietFoodDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        food = FoodItem.objects(id=id).first()
        if not food: return Response({"error": "Not Found"}, 404)
        
        # Check if we have deep details (Using 'description' as proxy for long desc)
        # Or better, just generate it on the fly and cache it in a new field if possible, 
        # or just return it.
        
        from ai.services.food_generator import generate_food_deep_dive
        
        # If description is short, assume we need a deep dive
        # Ideally we add a 'deep_dive_data' DictField to model, but for now let's just 
        # return the AI generated data directly.
        
        ai_data = generate_food_deep_dive(food.name)
        
        # Merge with existing data
        response_data = FoodItemSerializer(food).data
        response_data['deep_dive'] = ai_data
        
        # Fix image if broken or using unsplash (basic check)
        img_url = response_data.get('image_url', "")
        if not img_url or "unsplash" in img_url:
             # Fallback if unsplash links are dead
             s_name = food.name.replace(" ", "+")
             response_data['image_url'] = f"https://placehold.co/600x400/2a2a35/FFF?text={s_name}"
        
        return Response(response_data)

class CalculateMacrosView(APIView):
    """
    Takes natural language food log and returns estimated nutrition via AI.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response({"error": "Text is required"}, 400)
        
        # Lazy import
        from ai.services.food_generator import calculate_macros_from_text
        
        result = calculate_macros_from_text(text)
        
        if "error" in result:
             return Response(result, 500)
             
        return Response(result)
