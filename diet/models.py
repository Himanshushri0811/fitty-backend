from mongoengine import Document, StringField, IntField, FloatField, BooleanField, ListField, EmbeddedDocument, EmbeddedDocumentField, ReferenceField, DateTimeField, CASCADE, DictField
from accounts.models import User
from datetime import datetime

class FoodItem(Document):
    """
    Database of Food Items (Indian Context focus) with Intelligence
    """
    name = StringField(required=True, unique=True)
    calories = IntField(required=True) # per unit
    protein = FloatField(default=0.0)
    carbs = FloatField(default=0.0)
    fats = FloatField(default=0.0)
    fiber = FloatField(default=0.0)
    
    # "1 katori", "100g", "1 piece"
    serving_unit = StringField(required=True) 
    
    type = StringField(choices=('Veg', 'Non-Veg', 'Egg', 'Vegan'), default='Veg')
    cuisine = StringField(default='Indian') # North Indian, South Indian, Continental
    
    # Intelligence Fields
    budget = StringField(choices=('Low', 'Medium', 'High'), default='Medium')
    
    # "Why this meal?"
    goal_tags = ListField(StringField(choices=('Fat Loss', 'Muscle Gain', 'Maintenance', 'Keto', 'Energy')))
    benefits = ListField(StringField()) # Explainable AI hooks: "High Fiber", "Satiety" e.g., ["High Fiber", "Satiety"]
    
    # SMART BOX Fields
    ai_persona_text = StringField() # AI-Generated "Hello X..."
    fitness_relevance = StringField() # "Best for pre-workout..."
    image_url = StringField() # Unsplash URL

    description = StringField() # "Rich in complex carbs..."
    
    # Deep Dive Cache (New)
    deep_dive_data = DictField()
    
    # Slotting & Practicality
    best_time = ListField(StringField(choices=('Breakfast', 'Lunch', 'Dinner', 'Snack')))
    prep_time = IntField(default=15) # minutes
    cooking_difficulty = StringField(choices=('Easy', 'Medium', 'Hard'), default='Medium')
    
    # Keywords
    tags = ListField(StringField()) 
    
    meta = {
        'collection': 'food_items',
        'strict': False,
        'indexes': [
            {'fields': ['$name', '$description', '$tags'], 'default_language': 'english'}
        ]
    }

class DietProfile(Document):
    """
    User's Diet Preferences & Goals
    """
    user = ReferenceField(User, reverse_delete_rule=CASCADE, unique=True)
    
    goal = StringField(choices=('Weight Loss', 'Muscle Gain', 'Maintenance'), required=True)
    diet_type = StringField(choices=('Veg', 'Non-Veg', 'Egg', 'Vegan'), required=True)
    
    # Budget Preference
    budget_level = StringField(choices=('Low', 'Medium', 'High'), default='Medium')

    # Calculated or Manual targets
    target_calories = IntField(required=True)
    target_protein = IntField()
    target_carbs = IntField()
    target_fats = IntField()
    
    water_target = IntField(default=8) # glasses
    
    allergies = ListField(StringField())
    dislikes = ListField(StringField())
    
    meta = {'collection': 'diet_profiles'}

class MealItem(EmbeddedDocument):
    """
    Single item in a planned meal
    """
    food_item = ReferenceField(FoodItem)
    quantity = FloatField(default=1.0) # Multiplier of serving_unit
    custom_name = StringField() # If food_item is missing, fallback text
    calories_snapshot = IntField() # Snapshot to avoid historical changes if DB updates

class DailyMealSlot(EmbeddedDocument):
    """
    Breakfast, Lunch, etc.
    """
    name = StringField(required=True) # Breakfast, Lunch, Dinner, Snack 1...
    items = ListField(EmbeddedDocumentField(MealItem))
    time = StringField() # "08:00 AM"
    is_eaten = BooleanField(default=False)

class DietPlan(Document):
    """
    Weekly generated plan
    """
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    start_date = DateTimeField(default=datetime.utcnow)
    is_active = BooleanField(default=True)
    
    # We store 7 days of data. 
    # Structure: Key = Day Name (Monday), Value = List of Slots
    schedule = ListField(EmbeddedDocumentField(DailyMealSlot)) # Simplified: Just a template for now? 
    # Actually, let's make it robust.
    # We will use a flexible structure or list of days.
    
    # Let's try a simpler approach for MVP: A template for the week.
    # Monday: {Breakfast: [...], Lunch: [...]}
    # But usually people eat same/similar things or rotate. 
    
    # Let's stick to the Plan -> Days structure if we want full detail.
    # For MVP, maybe just ONE plan that repeats? 
    # "Weekly Diet Plan" implies Mon-Sun could be different.
    
    monday = ListField(EmbeddedDocumentField(DailyMealSlot))
    tuesday = ListField(EmbeddedDocumentField(DailyMealSlot))
    wednesday = ListField(EmbeddedDocumentField(DailyMealSlot))
    thursday = ListField(EmbeddedDocumentField(DailyMealSlot))
    friday = ListField(EmbeddedDocumentField(DailyMealSlot))
    saturday = ListField(EmbeddedDocumentField(DailyMealSlot))
    sunday = ListField(EmbeddedDocumentField(DailyMealSlot))
    
    meta = {
        'collection': 'diet_plans',
        'indexes': ['user']
    }

class DailyDietLog(Document):
    """
    What user actually ate (Tracking)
    """
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    date = StringField(required=True) # YYYY-MM-DD
    
    consumed_meals = ListField(EmbeddedDocumentField(DailyMealSlot))
    
    total_calories = IntField(default=0)
    water_intake = IntField(default=0)
    
    meta = {
        'collection': 'diet_daily_logs',
        'indexes': [
            {'fields': ['user', 'date'], 'unique': True}
        ]
    }
