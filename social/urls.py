from django.urls import path
from .views import FeedView, PostCreateView, SocialProfileView, MyProfileView, UserPostListView

urlpatterns = [
    path('feed/', FeedView.as_view(), name='feed'),
    path('posts/', PostCreateView.as_view(), name='post-create'),
    path('profiles/me/', MyProfileView.as_view(), name='my-profile'),
    path('profile/<str:username>/', SocialProfileView.as_view(), name='profile-detail'),
    path('profile/<str:username>/posts/', UserPostListView.as_view(), name='user-posts'),
]
