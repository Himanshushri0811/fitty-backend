from mongoengine import Document, StringField, ReferenceField, IntField, CASCADE
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
