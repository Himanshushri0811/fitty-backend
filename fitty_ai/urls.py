from django.urls import path
from .views import FittyAgentView

urlpatterns = [
    path('agent/', FittyAgentView.as_view(), name='fitty_agent'),
]
