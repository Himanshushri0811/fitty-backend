from django.urls import path
from .views import WaterIntakeView, DailyPlanView

urlpatterns = [
    path('water-intake/', WaterIntakeView.as_view(), name='water-intake'),
    path('daily-plan/', DailyPlanView.as_view(), name='daily-plan'),
]
