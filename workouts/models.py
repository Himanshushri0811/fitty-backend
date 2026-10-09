import mongoengine as me
from datetime import datetime

class PostureRule(me.EmbeddedDocument):
    name = me.StringField(required=True)
    message = me.DictField(default=dict) # e.g. {"unsafe": "Too deep", "correct": "Good"}
    # Store check logic as metadata or a simple string if needed, 
    # but usually the frontend has the math. 
    # For now we store the configuration parameters.
    check_type = me.StringField() # e.g. "angle_range"
    keypoints = me.ListField(me.IntField()) # [11, 13, 15]
    min_val = me.FloatField(default=0.0)
    max_val = me.FloatField(default=180.0)

class Exercise(me.Document):
    meta = {'collection': 'exercises'}

    DIFFICULTY_CHOICES = ('Beginner', 'Intermediate', 'Advanced')
    MUSCLE_GROUPS = ('Chest', 'Back', 'Legs', 'Shoulders', 'Tricep', 'Bicep', 'Abs', 'Forearms', 'Cardio', 'Full Body')
    EQUIPMENT_CHOICES = ('None', 'Dumbbell', 'Barbell', 'Machine', 'Cable', 'Kettlebell', 'Band')

    name = me.StringField(required=True, unique=True)
    description = me.StringField()
    video_url = me.StringField()
    thumbnail_url = me.StringField()
    
    difficulty = me.StringField(choices=DIFFICULTY_CHOICES, default='Beginner')
    target_muscle_group = me.StringField(choices=MUSCLE_GROUPS)
    equipment_type = me.StringField(choices=EQUIPMENT_CHOICES, default='None')
    
    # Store dynamic posture config
    posture_rules = me.ListField(me.EmbeddedDocumentField(PostureRule))
    
    created_at = me.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return self.name

class ExerciseVideo(me.Document):
    meta = {'collection': 'exercise_videos'}
    
    exercise = me.ReferenceField(Exercise, required=True)
    video_url = me.StringField(required=True)
    cloudinary_public_id = me.StringField() # For deletion
    uploaded_at = me.DateTimeField(default=datetime.utcnow)
    uploaded_by = me.StringField() # User ID or name
    status = me.StringField(default='Uploaded', choices=('Uploaded', 'Pending'))
    
    def __str__(self):
        return f"Video for {self.exercise.name}"
    
class WorkoutExercise(me.EmbeddedDocument):
    exercise_name = me.StringField(required=True) # We store name or ID. Storing name is easier for NoSQL embedding if no strict join is needed.
    exercise_id = me.StringField() # Stores the ObjectId string of the Exercise
    sets = me.IntField(default=3)
    reps = me.StringField(default="12")
    rest_time_seconds = me.IntField(default=60)
    notes = me.StringField()

class DailyRoutine(me.EmbeddedDocument):
    day_name = me.StringField(required=True) # Monday, Tuesday...
    focus_area = me.StringField()
    exercises = me.ListField(me.EmbeddedDocumentField(WorkoutExercise))

class WorkoutPlan(me.Document):
    meta = {'collection': 'workout_plans'}

    user_id = me.StringField(required=True) # Store User's ObjectId as string
    name = me.StringField(default="Custom Plan")
    goal = me.StringField()
    experience_level = me.StringField()
    days_per_week = me.IntField(default=5)
    equipment_available = me.ListField(me.StringField())
    
    routines = me.ListField(me.EmbeddedDocumentField(DailyRoutine))
    
    is_active = me.BooleanField(default=True)
    created_at = me.DateTimeField(default=datetime.utcnow)

    # Helper to deactivate others
    @classmethod
    def set_active(cls, user_id, plan_id):
        cls.objects(user_id=user_id).update(set__is_active=False)
        cls.objects(id=plan_id).update(set__is_active=True)
