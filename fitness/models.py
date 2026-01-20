from mongoengine import Document, StringField, ReferenceField, IntField, CASCADE, EmbeddedDocument, EmbeddedDocumentField, MapField, ListField
from accounts.models import User


class Goal(Document):
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    name = StringField(required=True)
    description = StringField()

    meta = {'collection': 'fitness_goals'}

class WorkoutDay(Document):
    goal = ReferenceField(Goal, reverse_delete_rule=CASCADE)
    day_name = StringField(max_length=15) # Monday, etc.
    focus = StringField()
    order = IntField()

    meta = {'collection': 'workout_days'}

class Exercise(Document):
    name = StringField(required=True)
    target_muscle = StringField()

    meta = {'collection': 'exercises'}

class DayExercise(Document):
    workout_day = ReferenceField(WorkoutDay, reverse_delete_rule=CASCADE)
    exercise = ReferenceField(Exercise)
    section = StringField() # warmup, main, etc.
    sets = IntField()
    reps = StringField()
    rest_seconds = IntField()
    order = IntField()

    meta = {'collection': 'workout_day_exercises'}

class DailyIntake(EmbeddedDocument):
    glasses = IntField(default=0)
    total_ml = IntField(default=0)
    last_drink_at = StringField()

class WaterIntake(Document):
    user = ReferenceField(User, reverse_delete_rule=CASCADE, unique=True)
    records = MapField(EmbeddedDocumentField(DailyIntake))  # Key: "YYYY-MM-DD"
    
    meta = {'collection': 'water_intake'}

class PlanItem(EmbeddedDocument):
    id = StringField() # generated uuid
    time = StringField()
    title = StringField()
    type = StringField(choices=('workout', 'yoga', 'diet', 'recovery', 'other'))
    status = StringField(default='pending', choices=('pending', 'completed'))
    coach_note = StringField()

class DailyPlan(Document):
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    date = StringField(required=True) # YYYY-MM-DD
    items = ListField(EmbeddedDocumentField(PlanItem))
    coach_message = StringField()
    
    meta = {
        'collection': 'daily_plans',
        'indexes': [
            {'fields': ['user', 'date'], 'unique': True}
        ]
    }

