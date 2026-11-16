from rest_framework import serializers
from .models import FoodItem, DietProfile, DietPlan, DailyDietLog, DailyMealSlot, MealItem

class FoodItemSerializer(serializers.Serializer):
    """
    Read-only serializer for Food Database
    """
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    calories = serializers.IntegerField()
    protein = serializers.FloatField()
    carbs = serializers.FloatField()
    fats = serializers.FloatField()
    fiber = serializers.FloatField()
    serving_unit = serializers.CharField()
    type = serializers.CharField()
    cuisine = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    
    # Intelligence Fields
    budget = serializers.CharField()
    goal_tags = serializers.ListField(child=serializers.CharField())
    benefits = serializers.ListField(child=serializers.CharField())
    description = serializers.CharField()
    image_url = serializers.CharField(required=False, allow_null=True)
    
    # New Fields
    best_time = serializers.ListField(child=serializers.CharField())
    prep_time = serializers.IntegerField()
    cooking_difficulty = serializers.CharField()

class DietProfileSerializer(serializers.Serializer):
    """
    User Diet Profile Settings
    """
    goal = serializers.CharField()
    diet_type = serializers.CharField()
    budget_level = serializers.CharField(default='Medium')
    target_calories = serializers.IntegerField(required=False)
    water_target = serializers.IntegerField(default=8)
    allergies = serializers.ListField(child=serializers.CharField(), required=False)
    dislikes = serializers.ListField(child=serializers.CharField(), required=False)

    def create(self, validated_data):
        # Logic is handled in Views for association with User
        return DietProfile(**validated_data)
    
    def update(self, instance, validated_data):
        instance.goal = validated_data.get('goal', instance.goal)
        instance.diet_type = validated_data.get('diet_type', instance.diet_type)
        instance.budget_level = validated_data.get('budget_level', instance.budget_level)
        instance.target_calories = validated_data.get('target_calories', instance.target_calories)
        instance.water_target = validated_data.get('water_target', instance.water_target)
        instance.allergies = validated_data.get('allergies', instance.allergies)
        instance.dislikes = validated_data.get('dislikes', instance.dislikes)
        instance.save()
        return instance

class MealItemSerializer(serializers.Serializer):
    food_item_id = serializers.SerializerMethodField()
    def get_food_item_id(self, obj):
        return str(obj.food_item.id) if obj.food_item else None

    food_name = serializers.SerializerMethodField()
    custom_name = serializers.CharField(required=False)
    quantity = serializers.FloatField(default=1.0)
    
    # Calories: Use Snapshot if available, else fetch from Food Item
    calories = serializers.SerializerMethodField()
    calories_snapshot = serializers.IntegerField(required=False)
    protein_snapshot = serializers.FloatField(required=False)
    carbs_snapshot = serializers.FloatField(required=False)
    fats_snapshot = serializers.FloatField(required=False)

    def get_calories(self, obj):
        if getattr(obj, 'calories_snapshot', None) is not None:
            return obj.calories_snapshot
        # Fallback
        item = self.get_food_item(obj)
        return item.calories if item else 0
    
    # Nutritional Info (Fetched from FoodItem)
    protein = serializers.SerializerMethodField()
    carbs = serializers.SerializerMethodField()
    fats = serializers.SerializerMethodField()

    # Intelligence from relational FoodItem - Safe Access
    food_description = serializers.SerializerMethodField()
    food_goal_tags = serializers.SerializerMethodField()
    food_benefits = serializers.SerializerMethodField()
    food_budget = serializers.SerializerMethodField()
    food_prep_time = serializers.SerializerMethodField()
    food_image = serializers.SerializerMethodField()

    def get_food_image(self, obj):
        item = self.get_food_item(obj)
        return item.image_url if item and hasattr(item, 'image_url') else None


    def get_food_item(self, obj):
        try:
            return obj.food_item
        except:
            return None

    def get_food_name(self, obj):
        item = self.get_food_item(obj)
        return item.name if item else (obj.custom_name or "Unknown Item")

    def get_protein(self, obj):
        if getattr(obj, 'protein_snapshot', None) is not None:
            return obj.protein_snapshot
        item = self.get_food_item(obj)
        return item.protein if item else 0

    def get_carbs(self, obj):
        if getattr(obj, 'carbs_snapshot', None) is not None:
            return obj.carbs_snapshot
        item = self.get_food_item(obj)
        return item.carbs if item else 0

    def get_fats(self, obj):
        if getattr(obj, 'fats_snapshot', None) is not None:
            return obj.fats_snapshot
        item = self.get_food_item(obj)
        return item.fats if item else 0

    def get_food_description(self, obj):
        item = self.get_food_item(obj)
        return item.description if item else None

    def get_food_goal_tags(self, obj):
        item = self.get_food_item(obj)
        return item.goal_tags if item and hasattr(item, 'goal_tags') else []

    def get_food_benefits(self, obj):
        item = self.get_food_item(obj)
        return item.benefits if item and hasattr(item, 'benefits') else []

    def get_food_budget(self, obj):
        item = self.get_food_item(obj)
        return item.budget if item and hasattr(item, 'budget') else None

    def get_food_prep_time(self, obj):
        item = self.get_food_item(obj)
        return item.prep_time if item and hasattr(item, 'prep_time') else 15

class DailyConstraintSerializer(serializers.Serializer):
    name = serializers.CharField()
    items = MealItemSerializer(many=True)
    time = serializers.CharField(required=False)
    is_eaten = serializers.BooleanField(read_only=True)

class DietPlanSerializer(serializers.Serializer):
    start_date = serializers.DateTimeField(read_only=True)
    monday = DailyConstraintSerializer(many=True)
    tuesday = DailyConstraintSerializer(many=True)
    wednesday = DailyConstraintSerializer(many=True)
    thursday = DailyConstraintSerializer(many=True)
    friday = DailyConstraintSerializer(many=True)
    saturday = DailyConstraintSerializer(many=True)
    sunday = DailyConstraintSerializer(many=True)
