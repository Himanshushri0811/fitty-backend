from django.urls import path
from .views import (
    GymOwnerDashboardOverview, 
    MemberManagerView
)

urlpatterns = [
    # Dashboard Overview (Limits, Profit Simulation)
    path('dashboard/overview/', GymOwnerDashboardOverview.as_view(), name='gym_dashboard_overview'),
    
    # Member Management (Plan-enforced limits)
    path('members/', MemberManagerView.as_view(), name='gym_members'),
]
