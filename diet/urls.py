from django.urls import path
from .views import (
    DietProfileView, 
    WeeklyPlanView, 
    FoodSearchView, 
    ReplaceMealView, 
    SeedFoodView,
    DietCarouselView,
    DietFoodDetailView,
    CalculateMacrosView,
    LogFoodView,
    DailySummaryView,
    MarkMealEatenView,
    RemoveLogEntryView,
    WaterLogView
)
from .claude_views import (
    ClaudeDietChatView,
    ClaudeDietPlanView,
    ClaudeDietSuggestionsView,
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
    path('log-food/', LogFoodView.as_view(), name='log-food'),

    # Daily Tracking Endpoints
    path('daily-summary/', DailySummaryView.as_view(), name='diet-daily-summary'),
    path('mark-eaten/', MarkMealEatenView.as_view(), name='diet-mark-eaten'),
    path('log-food/remove/', RemoveLogEntryView.as_view(), name='diet-log-remove'),
    path('water/', WaterLogView.as_view(), name='diet-water'),

    # Claude Diet AI Endpoints
    path('claude-chat/', ClaudeDietChatView.as_view(), name='claude-diet-chat'),
    path('claude-plan/', ClaudeDietPlanView.as_view(), name='claude-diet-plan'),
    path('claude-suggestions/', ClaudeDietSuggestionsView.as_view(), name='claude-diet-suggestions'),
]
