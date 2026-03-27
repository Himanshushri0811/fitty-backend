from mongoengine import Document, StringField, DateTimeField, ReferenceField
from datetime import datetime
from accounts.models import User

class FittyConversation(Document):
    """
    Stores conversation history between the user and Fitty AI.
    Used for providing context to the LLM.
    """
    meta = {
        'collection': 'fitty_conversations',
        'indexes': [
            'user',
            'timestamp'
        ]
    }

    user = ReferenceField(User, required=True)
    session_id = StringField(default="fitty_main")
    message = StringField(required=True)
    response = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"
