from mongoengine import Document, StringField, DateTimeField, EmailField, ListField, EmbeddedDocument, EmbeddedDocumentField, BooleanField, IntField
from datetime import datetime

class ContactMessage(Document):
    name = StringField(required=True)
    email = EmailField(required=True)
    subject = StringField()
    message = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'support_messages'}

class LiveChatMessage(EmbeddedDocument):
    sender = StringField(required=True, choices=('visitor', 'agent'))
    content = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    read = BooleanField(default=False)

class LiveChatSession(Document):
    """
    Represents a live chat session between a visitor (or user) and the Gym Owner/Support.
    """
    visitor_id = StringField(required=True) # Cookie ID or User ID
    visitor_name = StringField(default="Guest")
    
    agent_id = StringField() # ID of the Gym Owner/Staff responding
    
    status = StringField(default='active', choices=('active', 'closed'))
    messages = ListField(EmbeddedDocumentField(LiveChatMessage))
    
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    # Unread count for Agent
    unread_count = IntField(default=0)

    meta = {
        'collection': 'live_chat_sessions',
        'indexes': [
            {'fields': ['visitor_id', '-updated_at']},
            {'fields': ['status', '-updated_at']}
        ]
    }

    def add_message(self, sender, content):
        msg = LiveChatMessage(sender=sender, content=content)
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        if sender == 'visitor':
            self.unread_count += 1
        self.save()
