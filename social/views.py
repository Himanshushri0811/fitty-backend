from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Post, SocialProfile, Like, Comment, Follow
from .serializers import PostSerializer, SocialProfileSerializer
import json

class FeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Very simple feed for now
        posts = Post.objects(is_active=True).order_by('-created_at')[:20]
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

class PostCreateView(APIView):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, username):
        profile = SocialProfile.objects(username=username).first()
        if not profile:
             return Response({"error": "Profile not found"}, status=404)
        return Response(SocialProfileSerializer(profile).data)
