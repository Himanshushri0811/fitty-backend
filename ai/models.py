from mongoengine import Document, StringField, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField, GenericReferenceField, IntField
from datetime import datetime

class ChatMessage(EmbeddedDocument):
    """
    Single message within a chat session.
    """
    role = StringField(required=True, choices=('user', 'model', 'system'))
    content = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    
    # Metadata for debugging or context tracing
    context_used = StringField() 

class ChatSession(Document):
    """
    A conversation thread with Fitty.
    Now supports both User and GymOwner via GenericReferenceField.
    """
    # User can be Reference to User or GymOwner
    user = GenericReferenceField(required=True)
    
    title = StringField(default="New Chat")
    messages = ListField(EmbeddedDocumentField(ChatMessage))
    
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    # Stats
    message_count = IntField(default=0)
    
    meta = {
        'collection': 'ai_chat_sessions',
        'indexes': [
            {'fields': ['user', '-updated_at']}, 
        ]
    }

    def add_message(self, role, content, context=None):
        msg = ChatMessage(role=role, content=content, context_used=context)
        self.messages.append(msg)
        self.message_count += 1
        self.updated_at = datetime.utcnow()
        self.save()
