import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Member
from accounts.models import GymOwner
from datetime import datetime, timedelta

def get_razorpay_client():
    """
    Returns a configured Razorpay client using settings.
    """
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

from subscriptions.service import SubscriptionService

class GymOwnerDashboardOverview(APIView):
    """
    Main Dashboard for Gym Owners. 
    Shows plan details, limits, and profitability simulation.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'GYM_OWNER':
            return Response({"error": "Only Gym Owners can access metrics"}, status=status.HTTP_403_FORBIDDEN)
            
        owner = request.user 
        limits = SubscriptionService.get_plan_limits(owner)
        
        # 1. Stats
        current_members = Member.objects(gym_owner=owner).count()
        paid_members = Member.objects(gym_owner=owner, fees_status='PAID').count()
        
        # 2. Profit Simulation
        current_revenue = paid_members * owner.monthly_fee_per_member
        pro_potential = 1000 * owner.monthly_fee_per_member
        
        return Response({
            "gym_details": {
                "name": owner.gym_name,
                "branding_logo": owner.branding_logo,
                "plan": owner.plan_type,
                "status": owner.subscription_status
            },
            "limits": {
                "max_members": limits['max_members'],
                "used_members": current_members,
                "assistant_usage": f"{owner.assistant_daily_usage}/{limits['assistant_daily_limit']}"
            },
            "metrics": {
                "total_members": current_members,
                "active_paid": paid_members,
                "revenue": current_revenue,
                "potential_revenue": pro_potential
            }
        })

class MemberManagerView(APIView):
    """
    CRUD for Gym Members stored in MongoDB
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'GYM_OWNER':
            return Response({"error": "Unauthorized"}, status=403)
            
        # Optional: Pagination here in future
        members = Member.objects(gym_owner=request.user)
        return Response([{
            "id": str(m.id),
            "name": m.name,
            "mobile": m.mobile,
            "fees_status": m.fees_status,
            "join_date": m.join_date,
            "plan_name": m.plan_name
        } for m in members])

    def post(self, request):
        owner = request.user
        
        # 1. Check Limits via Service
        if not SubscriptionService.can_add_member(owner):
             return Response({
                 "error": "Member limit reached for your plan.",
                 "code": "LIMIT_REACHED"
             }, status=403)
            
        try:
            m = Member(
                gym_owner=owner,
                name=request.data.get('name'),
                mobile=request.data.get('mobile'),
                email=request.data.get('email', ''),
                gender=request.data.get('gender', ''),
                dob=request.data.get('dob'),
                plan_name=request.data.get('plan_name', 'Monthly'),
                amount_paid=request.data.get('amount_paid', 0),
                fees_status=request.data.get('fees_status', 'PENDING'),
                notes=request.data.get('notes', '')
            )
            # Calculate due date if not provided (simple logic: +30 days)
            if not request.data.get('fees_due_date'):
                m.fees_due_date = datetime.now().date() + timedelta(days=30)
            else:
                m.fees_due_date = request.data.get('fees_due_date')
                
            m.save()
            owner.current_member_count = Member.objects(gym_owner=owner).count() # Sync count
            owner.save()
            
            return Response({"id": str(m.id), "status": "added"}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
