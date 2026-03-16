import datetime
from mongoengine import Document, StringField, IntField, DateTimeField, ListField, DictField, ReferenceField

class Mission(Document):
    user_id = StringField(required=True, db_index=True)
    title = StringField(required=True)
    difficulty = StringField(choices=('Beginner', 'Intermediate', 'Advanced'), default='Beginner')
    exercises = ListField(DictField())
    xp_reward = IntField(default=100)
    ai_strategy_message = StringField()
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    date_assigned = StringField(required=True)

    meta = {
        'collection': 'fitty_missions',
        'indexes': ['user_id', ('user_id', 'date_assigned')]
    }

class MissionProgress(Document):
    user_id = StringField(required=True, db_index=True)
    mission_id = ReferenceField(Mission, required=True)
    status = StringField(choices=('pending', 'completed', 'missed'), default='pending')
    completed_at = DateTimeField()

    meta = {
        'collection': 'mission_progress'
    }

class UserStats(Document):
    user_id = StringField(required=True, unique=True)
    xp = IntField(default=0)
    level = IntField(default=1)
    streak_days = IntField(default=0)
    last_mission_date = StringField()

    meta = {
        'collection': 'user_gamification_stats'
    }
