from django.urls import path
from .views import GymListView, TrainerListView, EventListView

urlpatterns = [
    path('gyms/', GymListView.as_view(), name='gym-list'),
    path('trainers/', TrainerListView.as_view(), name='trainer-list'),
    path('events/', EventListView.as_view(), name='event-list'),
]
