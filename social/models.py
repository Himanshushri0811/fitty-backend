from mongoengine import Document, StringField, EmailField, DateTimeField, BooleanField, IntField, ReferenceField, ListField, CASCADE
from datetime import datetime
from accounts.models import User

# Replacing TextField with StringField as MongoEngine uses StringField for text
TextField = StringField

class SocialProfile(Document):
    """
    Extended user profile for social features using MongoEngine
    """
    user = ReferenceField(User, unique=True, reverse_delete_rule=CASCADE)
    username = StringField(required=True, unique=True, min_length=3)
    bio = TextField(max_length=500)
    profile_picture = StringField() # URL or path
    
    fitness_goal = StringField()
    followers_count = IntField(default=0)
    following_count = IntField(default=0)
    posts_count = IntField(default=0)
    
    is_private = BooleanField(default=False)
    allow_messages = BooleanField(default=True)
    
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'social_profiles'}

class Post(Document):
    author = ReferenceField(User, reverse_delete_rule=CASCADE)
    post_type = StringField(default='text', choices=('text', 'image', 'workout', 'achievement', 'tip'))
    caption = TextField(max_length=2200)
    image = StringField()
    
    likes_count = IntField(default=0)
    comments_count = IntField(default=0)
    shares_count = IntField(default=0)
    
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'social_posts',
        'indexes': ['-created_at', 'author']
    }

class Like(Document):
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    post = ReferenceField(Post, reverse_delete_rule=CASCADE)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'social_likes',
        'unique_together': ('user', 'post')
    }

class Comment(Document):
    post = ReferenceField(Post, reverse_delete_rule=CASCADE)
    author = ReferenceField(User, reverse_delete_rule=CASCADE)
    text = TextField(required=True)
    parent = ReferenceField('self', reverse_delete_rule=CASCADE)
    
    likes_count = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    is_active = BooleanField(default=True)

    meta = {'collection': 'social_comments'}

class Follow(Document):
    follower = ReferenceField(User, reverse_delete_rule=CASCADE)
    following = ReferenceField(User, reverse_delete_rule=CASCADE)
    status = StringField(default='accepted', choices=('pending', 'accepted'))
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'social_follows',
        'unique_together': ('follower', 'following')
    }

class Message(Document):
    sender = ReferenceField(User, reverse_delete_rule=CASCADE)
    recipient = ReferenceField(User, reverse_delete_rule=CASCADE)
    text = TextField(required=True)
    is_read = BooleanField(default=False)
    read_at = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'social_messages',
        'indexes': ['-created_at']
    }

class Notification(Document):
    recipient = ReferenceField(User, reverse_delete_rule=CASCADE)
    actor = ReferenceField(User, reverse_delete_rule=CASCADE)
    notification_type = StringField(required=True)
    post = ReferenceField(Post)
    comment = ReferenceField(Comment)
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'social_notifications'}
