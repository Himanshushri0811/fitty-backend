from django.urls import path
from .views import DietProfileView, WeeklyPlanView, FoodSearchView, SeedFoodView, ReplaceMealView

urlpatterns = [
    path('profile/', DietProfileView.as_view(), name='diet-profile'),
    path('plan/', WeeklyPlanView.as_view(), name='diet-plan'),
    path('foods/search/', FoodSearchView.as_view(), name='food-search'),
    path('plan/replace/', ReplaceMealView.as_view(), name='meal-replace'),
    path('seed/', SeedFoodView.as_view(), name='seed-foods'),
]
