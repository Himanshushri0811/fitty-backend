from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.AIChatAPIView.as_view(), name="chat_with_fitty"),
    path("sessions/", views.AISessionListAPIView.as_view(), name="chat_sessions"),
    path("sessions/<str:id>/", views.AISessionDetailAPIView.as_view(), name="chat_session_detail"),
    path("posture-analysis/", views.PostureAnalysisAPIView.as_view(), name="posture_analysis"),
]
