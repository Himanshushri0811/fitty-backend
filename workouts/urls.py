from django.urls import path
from .views import (
    GenerateWorkoutPlanView, 
    ActiveWorkoutPlanView, 
    SaveWorkoutPlanView,
    ExerciseLibraryView,
    ExerciseListView, 
    ExerciseDetailView, 
    AdminExerciseVideoUploadView,
    AdminExerciseVideoDeleteView,
    AdminExerciseVideoReplaceView,
    AdminVideoListView
)

urlpatterns = [
    path('generate/', GenerateWorkoutPlanView.as_view(), name='generate-workout'),
    path('current/', ActiveWorkoutPlanView.as_view(), name='current-plan'),
    path('save/', SaveWorkoutPlanView.as_view(), name='save-plan'),
    path('library/', ExerciseLibraryView.as_view(), name='exercise-library'),
    path('exercises/', ExerciseListView.as_view(), name='exercise-list'),
    path('exercises/<str:id>/', ExerciseDetailView.as_view(), name='exercise-detail'),
    
    # Admin Video Management
    path('admin/videos/', AdminVideoListView.as_view(), name='admin-video-list'),
    path('admin/videos/upload/', AdminExerciseVideoUploadView.as_view(), name='admin-video-upload'),
    path('admin/videos/replace/', AdminExerciseVideoReplaceView.as_view(), name='admin-video-replace'),
    path('admin/videos/delete/<str:id>/', AdminExerciseVideoDeleteView.as_view(), name='admin-video-delete'),
]
