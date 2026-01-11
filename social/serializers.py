from rest_framework import serializers
from .models import SocialProfile, Post, Like, Comment, Follow, Message, Notification

class SocialProfileSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    username = serializers.CharField()
    bio = serializers.CharField(required=False, allow_blank=True)
    profile_picture = serializers.CharField(required=False, allow_blank=True)
    fitness_goal = serializers.CharField(required=False, allow_blank=True)
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    posts_count = serializers.IntegerField(read_only=True)
    is_private = serializers.BooleanField(default=False)
    created_at = serializers.DateTimeField(read_only=True)

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
