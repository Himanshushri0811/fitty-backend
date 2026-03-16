from django.urls import path
from .views import TodayMissionView, CompleteMissionView

urlpatterns = [
    path("today/", TodayMissionView.as_view(), name="missions-today"),
    path("<str:mission_id>/complete/", CompleteMissionView.as_view(), name="missions-complete"),
]
