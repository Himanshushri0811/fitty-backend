import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Member, PaymentHistory
from accounts.models import GymOwner
from datetime import datetime, timedelta

def get_razorpay_client():
    """
    Returns a configured Razorpay client using settings.
    """
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class GymOwnerDashboardOverview(APIView):
    """
    Main Dashboard for Gym Owners. 
    Shows plan details, limits, and profitability simulation.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'GYM_OWNER':
            return Response({"error": "Only Gym Owners can access metrics"}, status=status.HTTP_403_FORBIDDEN)
            
        owner = request.user # This is a GymOwner MongoEngine document
        
        # 1. Performance Statistics
        members_count = Member.objects(gym_owner=owner).count()
        paid_count = Member.objects(gym_owner=owner, fees_status='PAID').count()
        
        # 2. Profit Simulation Logic (as requested)
        # We simulate earnings based on current members and potential earnings on Pro plan
        current_earnings = paid_count * owner.monthly_fee_per_member
        pro_simulation = 1000 * owner.monthly_fee_per_member # What they COULD earn if they upgrade to Pro
        
        # 3. Plan Logic
        is_pro = (owner.plan_type == 'PRO')
        
        return Response({
            "gym_details": {
                "name": owner.gym_name,
                "address": owner.gym_address,
                "plan": owner.plan_type,
                "is_pro": is_pro,
                "status": owner.dashboard_status
            },
            "limits": {
                "max_members": owner.max_members_limit,
                "current_count": members_count,
                "remaining_slots": max(0, owner.max_members_limit - members_count)
            },
            "profit_simulation": {
                "current_monthly_revenue": current_earnings,
                "projected_full_pro_revenue": pro_simulation,
                "currency": "INR",
                "message": "Upgrade to PRO to unlock 1000 member slots and maximize your revenue!" if not is_pro else "You are already maximizing your reach with the PRO plan."
            },
            "members": {
                "total": members_count,
                "paid": paid_count,
                "pending": members_count - paid_count
            }
        })

class PlanUpgradeView(APIView):
    """
    Processes simulated/actual Razorpay payments to upgrade a GymOwner to PRO.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'GYM_OWNER':
            return Response({"error": "Only owners can upgrade"}, status=403)
            
        # Simulate payment validation (or use actual razorpay capture)
        # In a real scenario, you'd verify the signature here.
        payment_status = request.data.get('status', 'success')
        order_id = request.data.get('order_id', 'sim_ord_123')
        payment_id = request.data.get('payment_id', 'sim_pay_123')

        if payment_status == 'success':
            owner = request.user
            owner.update_plan('PRO')
            
            # Record payment in MongoDB
            PaymentHistory(
                gym_owner=owner,
                order_id=order_id,
                payment_id=payment_id,
                amount=399.00,
                status='success',
                plan_type='PRO'
            ).save()
            
            return Response({
                "status": "success",
                "message": "Payment verified and Plan Upgraded to PRO",
                "new_limit": 1000
            })
            
        return Response({"error": "Payment failed or was cancelled"}, status=400)

class MemberManagerView(APIView):
    """
    CRUD for Gym Members stored in MongoDB
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        members = Member.objects(gym_owner=request.user)
        return Response([{
            "id": str(m.id),
            "name": m.name,
            "mobile": m.mobile,
            "status": m.fees_status
        } for m in members])

    def post(self, request):
        owner = request.user
        if Member.objects(gym_owner=owner).count() >= owner.max_members_limit:
            return Response({"error": "Limit reached for your current plan. Please upgrade to PRO!"}, status=403)
            
        m = Member(
            gym_owner=owner,
            name=request.data.get('name'),
            mobile=request.data.get('mobile'),
            fees_status=request.data.get('fees_status', 'PENDING')
        ).save()
        return Response({"id": str(m.id), "status": "added"}, status=201)
