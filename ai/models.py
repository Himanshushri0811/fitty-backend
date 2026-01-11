from mongoengine import Document, StringField, DateTimeField, ReferenceField
from datetime import datetime
from accounts.models import User

class ChatMessage(Document):
    user = ReferenceField(User)
    message = StringField(required=True)
    response = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'ai_chat_messages'}
