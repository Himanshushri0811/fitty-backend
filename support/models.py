from mongoengine import Document, StringField, DateTimeField, EmailField
from datetime import datetime

class ContactMessage(Document):
    name = StringField(required=True)
    email = EmailField(required=True)
    subject = StringField()
    message = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'support_messages'}
