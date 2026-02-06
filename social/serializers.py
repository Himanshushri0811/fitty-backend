from rest_framework import serializers
from .models import SocialProfile, Post, Like, Comment, Follow, Message, Notification

class SocialProfileSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    username = serializers.CharField()
    full_name = serializers.SerializerMethodField()
    profile_picture_url = serializers.CharField(source='profile_picture', required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    def get_full_name(self, obj):
        return getattr(obj.user, 'name', obj.username)
    profile_picture = serializers.CharField(required=False, allow_blank=True)
    fitness_goal = serializers.CharField(required=False, allow_blank=True)
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    posts_count = serializers.IntegerField(read_only=True)
    is_private = serializers.BooleanField(default=False)
    is_following = serializers.SerializerMethodField()
    follows_you = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    join_date = serializers.DateTimeField(source='created_at', read_only=True)

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        from .models import Follow
        return Follow.objects(follower=request.user, following=obj.user, status='accepted').first() is not None

    def get_follows_you(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        from .models import Follow
        return Follow.objects(follower=obj.user, following=request.user, status='accepted').first() is not None

class PostSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    author_id = serializers.CharField(source='author.id', read_only=True)
    post_type = serializers.CharField()
    caption = serializers.CharField()
    image = serializers.CharField(required=False, allow_null=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

class CommentSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    post_id = serializers.CharField(source='post.id', read_only=True)
    author_id = serializers.CharField(source='author.id', read_only=True)
    text = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)

class FollowSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    follower_id = serializers.CharField(source='follower.id', read_only=True)
    following_id = serializers.CharField(source='following.id', read_only=True)
    status = serializers.CharField()
