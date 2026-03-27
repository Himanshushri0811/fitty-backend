from django.urls import path
from .views import FittyAgentView, FittySessionListView, FittySessionDetailView

urlpatterns = [
    path('agent/', FittyAgentView.as_view(), name='fitty_agent'),
    path('sessions/', FittySessionListView.as_view(), name='fitty_sessions'),
    path('sessions/<str:session_id>/', FittySessionDetailView.as_view(), name='fitty_session_detail'),
]
