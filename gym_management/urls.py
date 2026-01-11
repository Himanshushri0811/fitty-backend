from django.urls import path
from .views import (
    GymOwnerDashboardOverview, 
    MemberManagerView, 
    PlanUpgradeView
)

urlpatterns = [
    # Dashboard Overview (Limits, Profit Simulation)
    path('dashboard/overview/', GymOwnerDashboardOverview.as_view(), name='gym_dashboard_overview'),
    
    # Member Management (Plan-enforced limits)
    path('members/', MemberManagerView.as_view(), name='gym_members'),
    
    # Plan Upgrade (Razorpay/Stripe simulation)
    path('plan/upgrade/', PlanUpgradeView.as_view(), name='plan_upgrade'),
]
