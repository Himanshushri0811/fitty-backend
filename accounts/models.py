from mongoengine import Document, StringField, EmailField, DateTimeField, BooleanField, IntField, FloatField, DecimalField, EmbeddedDocument, EmbeddedDocumentListField, ListField, DateField, EmbeddedDocumentField
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password as django_check_password

class WorkoutExercise(EmbeddedDocument):
    name = StringField(required=True)
    sets = StringField()
    reps = StringField()
    description = StringField()
    video_url = StringField(default="") # Link to user's uploaded video

class WorkoutDay(EmbeddedDocument):
    day_name = StringField(required=True) # Monday, Tuesday, etc.
    focus = StringField(required=True)
    exercises = EmbeddedDocumentListField(WorkoutExercise)

class WorkoutFeedback(EmbeddedDocument):
    date = DateTimeField(default=datetime.utcnow)
    workout_day_index = IntField() # 0-6
    difficulty = StringField(choices=('Easy', 'Medium', 'Hard'))
    fatigue_level = IntField(min_value=1, max_value=10)
    form_quality = StringField(choices=('Good', 'Needs Improvement', 'Poor'))

class WeightLog(EmbeddedDocument):
    date = DateTimeField(default=datetime.utcnow)
    weight = FloatField(required=True)

class DailyCalorieLog(EmbeddedDocument):
    date = DateField(default=datetime.utcnow) # Only one entry per day
    calories_burned = FloatField(default=0.0)
    calories_consumed = FloatField(default=0.0)
    water_intake_glasses = IntField(default=0)

class User(Document):
    """
    Unified User Model for Athletes and Gym Owners.
    Single Source of Truth.
    """
    meta = {
        'collection': 'users',
        'indexes': [
            'email',
            'username',
            'role' 
        ]
    }
    
    # Core Auth Fields
    email = EmailField(required=True, unique=True)
    username = StringField(required=True, unique=True) # For GymOwners, we can auto-fill this with email part if not provided
    password = StringField(required=True)
    role = StringField(required=True, default='USER', choices=('USER', 'GYM_OWNER')) 
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    
    # Common Profile Fields
    name = StringField() 
    profile_pic = StringField(default="") 
    cover_pic = StringField(default="") 

    # --- Athlete (Normal User) Specific Fields ---
    goal = StringField()
    age = IntField()
    gender = StringField()
    height = FloatField()
    weight = FloatField()
    bio = StringField()
    fitness_level = StringField(default='Beginner')
    weekly_plan = EmbeddedDocumentListField(WorkoutDay)
    workout_history = EmbeddedDocumentListField(WorkoutFeedback)
    workouts_completed = IntField(default=0)
    
    # Extended Profile Fields
    mobile = StringField()
    dob = DateField()
    activity_level = StringField(choices=('Sedentary', 'Lightly Active', 'Moderately Active', 'Very Active', 'Super Active'), default='Moderately Active')
    
    # Phase 1 Enhancements
    target_weight = FloatField()
    diet_preference = StringField(choices=('Vegetarian', 'Non-Vegetarian', 'Vegan', 'Eggetarian', 'Keto', 'Other'), default='Non-Vegetarian')
    medical_conditions = ListField(StringField(), default=list)
    allergies = ListField(StringField(), default=list)
    preferred_workout_type = StringField(choices=('Gym', 'Yoga', 'Home Workout', 'Cardio', 'Calisthenics'), default='Gym')
    
    # Tracking Data
    weight_history = ListField(EmbeddedDocumentField('WeightLog'), default=list)
    daily_calories_log = ListField(EmbeddedDocumentField('DailyCalorieLog'), default=list)
    
    # Password Reset Fields
    reset_password_token = StringField()
    reset_password_expiry = DateTimeField()

    # --- Gym Owner Specific Fields ---
    gym_name = StringField()
    gym_address = StringField()
    plan_type = StringField(default='FREE', choices=('FREE', 'PRO')) 
    plan_expiry = DateTimeField()
    is_pro_active = BooleanField(default=False)
    subscription_status = StringField(default='ACTIVE', choices=('ACTIVE', 'PAST_DUE', 'CANCELLED'))
    branding_logo = StringField(default="")
    
    # Gym Simulation Data
    monthly_fee_per_member = FloatField(default=500.0) 
    current_profit = FloatField(default=0.0) 
    max_members_limit = IntField(default=25) # 25 for FREE, 1000 for PRO
    current_member_count = IntField(default=0)
    dashboard_status = StringField(default='ACTIVE')

    # Assistant Usage Tracking (Common)
    assistant_daily_usage = IntField(default=0)
    last_assistant_usage_date = DateField()

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)

    @property
    def is_authenticated(self):
        return True

    # Gym Owner Helper Methods
    def update_plan(self, plan_name):
        self.plan_type = plan_name
        self.is_pro_active = (plan_name == 'PRO')
        if plan_name == 'PRO':
            self.max_members_limit = 1000
        else:
            self.max_members_limit = 25
        self.save()

    def calculate_simulation(self):
        return self.current_member_count * self.monthly_fee_per_member

# For backward compatibility / ease of refactoring, 
# although we should update usages to User.objects(role='GYM_OWNER')
# We cannot easily alias a filtered QuerySet to a class name in Python at module level for imports.
# But we can alias the class for type checking or direct instantiation (though logic differs).
GymOwner = User 
