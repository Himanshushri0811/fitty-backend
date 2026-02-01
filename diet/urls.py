from django.urls import path
from .views import (
    DietProfileView, 
    WeeklyPlanView, 
    FoodSearchView, 
    ReplaceMealView, 
    SeedFoodView,
    DietCarouselView,
    DietFoodDetailView,
    CalculateMacrosView
)

urlpatterns = [
    path('profile/', DietProfileView.as_view(), name='diet-profile'),
    path('plan/', WeeklyPlanView.as_view(), name='diet-plan'),
    path('food-search/', FoodSearchView.as_view(), name='food-search'),
    path('replace-meal/', ReplaceMealView.as_view(), name='diet-replace-meal'),
    path('seed/', SeedFoodView.as_view(), name='diet-seed'),
    
    # AI Smart Box Endpoints
    path('carousel/', DietCarouselView.as_view(), name='diet-carousel'),
    path('foods/<str:id>/', DietFoodDetailView.as_view(), name='diet-food-detail'),
    path('calculate-macros/', CalculateMacrosView.as_view(), name='calculate-macros'),
]
