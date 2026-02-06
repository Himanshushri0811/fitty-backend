from rest_framework import serializers
from .models import User, GymOwner

class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField(read_only=True)
    goal = serializers.CharField(required=False)
    mobile = serializers.CharField(required=False)
    activity_level = serializers.CharField(required=False)
    
class GymOwnerSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    gym_name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField(read_only=True)
    plan_type = serializers.CharField(read_only=True)
    is_pro_active = serializers.BooleanField(read_only=True)
    max_members = serializers.IntegerField(read_only=True)
