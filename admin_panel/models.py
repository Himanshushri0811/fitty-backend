from mongoengine import Document, StringField, DateTimeField
from datetime import datetime

class AdminActionLog(Document):
    admin_email = StringField()
    action = StringField()
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'admin_logs'}
