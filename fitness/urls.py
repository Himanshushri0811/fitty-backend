from django.urls import path
from .views import WaterIntakeView, DailyPlanView, ExerciseDetailView, ExerciseListView

urlpatterns = [
    path('water-intake/', WaterIntakeView.as_view(), name='water-intake'),
    path('daily-plan/', DailyPlanView.as_view(), name='daily-plan'),
    path('exercises/', ExerciseListView.as_view(), name='exercise-list'),
    path('exercises/<str:name>/', ExerciseDetailView.as_view(), name='exercise-detail'),
]
