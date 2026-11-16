from mongoengine import (
    Document, StringField, IntField, FloatField, BooleanField, ListField,
    EmbeddedDocument, EmbeddedDocumentField, ReferenceField, DateTimeField,
    CASCADE, DictField,
)
from accounts.models import User
from datetime import datetime


class FoodItem(Document):
    """
    Database of Food Items (Indian Context focus) with Intelligence
    """
    name = StringField(required=True, unique=True)
    calories = IntField(required=True)  # per unit
    protein = FloatField(default=0.0)
    carbs = FloatField(default=0.0)
    fats = FloatField(default=0.0)
    fiber = FloatField(default=0.0)

    # "1 katori", "100g", "1 piece"
    serving_unit = StringField(required=True)

    type = StringField(choices=('Veg', 'Non-Veg', 'Egg', 'Vegan'), default='Veg')
    cuisine = StringField(default='Indian')  # North Indian, South Indian, Continental

    # Intelligence Fields
    budget = StringField(choices=('Low', 'Medium', 'High'), default='Medium')

    # "Why this meal?"
    goal_tags = ListField(StringField(choices=('Fat Loss', 'Muscle Gain', 'Maintenance', 'Keto', 'Energy')))
    benefits = ListField(StringField())

    # SMART BOX Fields
    ai_persona_text = StringField()
    fitness_relevance = StringField()
    image_url = StringField()

    description = StringField()

    # Deep Dive Cache
    deep_dive_data = DictField()

    # Slotting & Practicality
    best_time = ListField(StringField(choices=('Breakfast', 'Lunch', 'Dinner', 'Snack')))
    prep_time = IntField(default=15)  # minutes
    cooking_difficulty = StringField(choices=('Easy', 'Medium', 'Hard'), default='Medium')

    # Keywords (allergen matching bhi inhi se hota hai: 'milk', 'nuts', 'egg', 'gluten' ...)
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

    budget_level = StringField(choices=('Low', 'Medium', 'High'), default='Medium')

    # Calculated or Manual targets
    target_calories = IntField(required=True)
    target_protein = IntField()
    target_carbs = IntField()
    target_fats = IntField()

    water_target = IntField(default=8)  # glasses

    allergies = ListField(StringField())
    dislikes = ListField(StringField())

    meta = {'collection': 'diet_profiles'}


class MealItem(EmbeddedDocument):
    """
    Single item in a planned meal.
    NOTE: calories_snapshot (aur naye *_snapshot) = is item ke TOTAL (quantity ke saath).
    Frontend ko quantity se dobara multiply NAHI karna hai.
    """
    food_item = ReferenceField(FoodItem)
    quantity = FloatField(default=1.0)  # Multiplier of serving_unit
    custom_name = StringField()
    calories_snapshot = IntField()
    protein_snapshot = FloatField(default=0.0)   # NEW
    carbs_snapshot = FloatField(default=0.0)     # NEW
    fats_snapshot = FloatField(default=0.0)      # NEW


class DailyMealSlot(EmbeddedDocument):
    """
    Breakfast, Lunch, etc.
    """
    name = StringField(required=True)
    items = ListField(EmbeddedDocumentField(MealItem))
    time = StringField()  # "08:00 AM"
    is_eaten = BooleanField(default=False)  # legacy; ab 'eaten' DailyDietLog.entries (ref='plan:<slot>') se aata hai


class DietPlan(Document):
    """
    Weekly generated plan
    """
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    start_date = DateTimeField(default=datetime.utcnow)
    is_active = BooleanField(default=True)

    schedule = ListField(EmbeddedDocumentField(DailyMealSlot))  # legacy, unused

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


class LoggedEntry(EmbeddedDocument):
    """
    Ek log (user ne kya khaya). Daily totals inhi se banta hai (single source of truth).
    ref = 'plan:<SlotName>' agar plan ka meal 'eaten' mark kiya gaya, warna khali.
    """
    entry_id = StringField(required=True)
    client_id = StringField()          # frontend ka UUID: double-click par double count nahi hoga
    ref = StringField(default='')
    meal_type = StringField(default='Snack')
    time = StringField()
    text = StringField()
    items = ListField(DictField())
    calories = FloatField(default=0.0)
    protein = FloatField(default=0.0)
    carbs = FloatField(default=0.0)
    fats = FloatField(default=0.0)
    fiber = FloatField(default=0.0)
    source = StringField(default='manual')   # ai | db | plan | manual
    created_at = DateTimeField(default=datetime.utcnow)


class DailyDietLog(Document):
    """
    What user actually ate (Tracking)
    """
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    date = StringField(required=True)  # YYYY-MM-DD

    consumed_meals = ListField(EmbeddedDocumentField(DailyMealSlot))  # legacy

    entries = ListField(EmbeddedDocumentField(LoggedEntry))           # NEW
    legacy_calories = IntField(default=0)                             # NEW: purane logs ki calories

    total_calories = IntField(default=0)
    total_protein = FloatField(default=0.0)                           # NEW
    total_carbs = FloatField(default=0.0)                             # NEW
    total_fats = FloatField(default=0.0)                              # NEW
    total_fiber = FloatField(default=0.0)                             # NEW
    water_intake = IntField(default=0)

    meta = {
        'collection': 'diet_daily_logs',
        'indexes': [
            {'fields': ['user', 'date'], 'unique': True}
        ]
    }

    def recompute(self):
        ents = self.entries or []
        self.total_calories = int(round((self.legacy_calories or 0) + sum((e.calories or 0) for e in ents)))
        self.total_protein = round(sum((e.protein or 0) for e in ents), 1)
        self.total_carbs = round(sum((e.carbs or 0) for e in ents), 1)
        self.total_fats = round(sum((e.fats or 0) for e in ents), 1)
        self.total_fiber = round(sum((e.fiber or 0) for e in ents), 1)
