from django.urls import path
from .views import FeedView, PostCreateView, SocialProfileView

urlpatterns = [
    path('feed/', FeedView.as_view(), name='feed'),
    path('posts/', PostCreateView.as_view(), name='post-create'),
    path('profile/<str:username>/', SocialProfileView.as_view(), name='profile-detail'),
]
