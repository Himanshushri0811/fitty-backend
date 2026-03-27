from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Post, SocialProfile, Like, Comment, Follow
from .serializers import PostSerializer, SocialProfileSerializer
from accounts.models import User
import json

class FeedView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Very simple feed for now
        posts = Post.objects(is_active=True).order_by('-created_at')[:20]
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

class PostCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        post = Post(
            author=request.user,
            post_type=data.get('post_type', 'text'),
            caption=data.get('caption'),
            image=data.get('image')
        )
        post.save()
        return Response(PostSerializer(post).data, status=201)

class SocialProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        profile = SocialProfile.objects(username=username).first()
        
        if not profile:
            # Check if user exists in accounts and create social profile
            user = User.objects(username=username).first()
            if not user:
                return Response({"error": "Profile not found"}, status=404)
            
            # Create SocialProfile for the existing user
            profile = SocialProfile(
                user=user,
                username=user.username,
                fitness_goal=getattr(user, 'goal', 'Get Fit')
            )
            profile.save()
            
        return Response(SocialProfileSerializer(profile, context={'request': request}).data)

class MyProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        profile = SocialProfile.objects(user=request.user).first()
        if not profile:
            # Create default profile if missing
            # Ensure unique username by falling back to user.username (if exists) or name/email
            # GymOwner might not have username
            username = getattr(request.user, 'username', None)
            if not username:
                if hasattr(request.user, 'email'):
                    username = request.user.email.split('@')[0]
                elif hasattr(request.user, 'name'):
                    username = request.user.name.replace(" ", "_").lower()
                else:
                    username = f"user_{str(request.user.id)[:8]}"
            
            # Check if this username is already taken by another social profile
            if SocialProfile.objects(username=username).first():
                 username = f"{username}_{str(request.user.id)[:4]}"

            profile = SocialProfile(
                user=request.user,
                username=username,
                fitness_goal=getattr(request.user, 'goal', 'Get Fit')
            )
            profile.save()
        
        return Response(SocialProfileSerializer(profile).data)

class UserPostListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        user = User.objects(username=username).first()
        if not user:
            return Response({"error": "User not found"}, status=404)
        
        posts = Post.objects(author=user, is_active=True).order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
