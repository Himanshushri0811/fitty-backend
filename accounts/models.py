from mongoengine import Document, StringField, EmailField, DateTimeField, BooleanField, IntField, FloatField, DecimalField
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password as django_check_password

class FitMitraUser(Document):
    """
    Base User Document for Pure Mongo Auth
    No SQL dependencies. Optimized for MongoDB Atlas TLS.
    """
    meta = {
        'allow_inheritance': True,
        'indexes': ['email'],
        'abstract': True
    }
    
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    role = StringField(required=True) # USER, GYM_OWNER

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)

    @property
    def is_authenticated(self):
        return True

class User(FitMitraUser):
    meta = {'collection': 'users'}
    username = StringField(required=True, unique=True)
    
    # Profile stats
    goal = StringField()
    age = IntField()
    gender = StringField()
    fitness_level = StringField(default='Beginner')

class GymOwner(FitMitraUser):
    meta = {'collection': 'gym_owners'}
    gym_name = StringField(required=True)
    gym_address = StringField()

    # Subscription & Dashboard Logic
    plan_type = StringField(default='FREE', choices=('FREE', 'PRO')) 
    plan_expiry = DateTimeField()
    is_pro_active = BooleanField(default=False)
    
    # Simulation Data
    monthly_fee_per_member = FloatField(default=500.0) # Simulation base
    current_profit = FloatField(default=0.0) 
    
    # Operational Limits
    max_members_limit = IntField(default=25) # 25 for FREE, 1000 for PRO
    current_member_count = IntField(default=0)
    
    dashboard_status = StringField(default='ACTIVE')

    def update_plan(self, plan_name):
        self.plan_type = plan_name
        self.is_pro_active = (plan_name == 'PRO')
        if plan_name == 'PRO':
            self.max_members_limit = 1000
        else:
            self.max_members_limit = 25
        self.save()

    def calculate_simulation(self):
        """
        Calculates potential profit based on member count and fee
        """
        return self.current_member_count * self.monthly_fee_per_member
