from mongoengine import Document, StringField, DecimalField, IntField, ListField, DateTimeField, ReferenceField, BooleanField, CASCADE, DateField
from datetime import datetime
from accounts.models import User

TextField = StringField

class Gym(Document):
    name = StringField(required=True)
    description = TextField()
    address = StringField()
    city = StringField()
    latitude = DecimalField(precision=6)
    longitude = DecimalField(precision=6)
    rating = DecimalField(precision=2, default=0.0)
    price_range_min = DecimalField(precision=2)
    price_range_max = DecimalField(precision=2)
    thumbnail = StringField()
    facilities = ListField(StringField())
    contact_number = StringField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'explore_gyms'}

class Trainer(Document):
    name = StringField(required=True)
    specialization = StringField(default="General Fitness")
    bio = TextField()
    image = StringField()
    experience_years = IntField(default=1)

    meta = {'collection': 'explore_trainers'}

class Event(Document):
    title = StringField(required=True)
    description = TextField()
    banner = StringField()
    start_time = DateTimeField()
    end_time = DateTimeField()
    trainer = ReferenceField(Trainer)
    status = StringField(default='upcoming', choices=('upcoming', 'live', 'completed'))
    participants_count = IntField(default=0)

    meta = {'collection': 'explore_events'}

class Challenge(Document):
    title = StringField(required=True)
    description = TextField()
    banner = StringField()
    duration_days = IntField()
    difficulty = StringField(choices=('beginner', 'intermediate', 'advanced'))
    start_date = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'explore_challenges'}

class Article(Document):
    title = StringField(required=True)
    content = TextField()
    author = ReferenceField(Trainer)
    image = StringField()
    read_time_minutes = IntField(default=5)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'explore_articles'}

class UserEvent(Document):
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    event = ReferenceField(Event, reverse_delete_rule=CASCADE)
    joined_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_joined_events',
        'unique_together': ('user', 'event')
    }
