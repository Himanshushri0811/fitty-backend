import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
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
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

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

    def put(self, request):
        """
        Update member details
        """
        if request.user.role != 'GYM_OWNER':
            return Response({"error": "Unauthorized"}, status=403)
            
        member_id = request.data.get('id')
        if not member_id:
            return Response({"error": "Member ID required"}, status=400)
            
        try:
            m = Member.objects.get(id=member_id, gym_owner=request.user)
            
            # Update fields if present
            fields = ['name', 'mobile', 'email', 'gender', 'dob', 'plan_name', 'fees_status', 'fees_due_date', 'notes']
            for field in fields:
                if field in request.data:
                    setattr(m, field, request.data[field])
            
            m.save()
            return Response({"status": "updated"}, status=200)
        except Member.DoesNotExist:
            return Response({"error": "Member not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def delete(self, request):
        """
        Delete a member
        """
        if request.user.role != 'GYM_OWNER':
            return Response({"error": "Unauthorized"}, status=403)
            
        member_id = request.query_params.get('id')
        if not member_id:
             return Response({"error": "Member ID required"}, status=400)
             
        try:
            m = Member.objects.get(id=member_id, gym_owner=request.user)
            m.delete()
            
            # Update count
            request.user.current_member_count = Member.objects(gym_owner=request.user).count()
            request.user.save()
            
            return Response({"status": "deleted"}, status=200)
        except Member.DoesNotExist:
            return Response({"error": "Member not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class GymProfileView(APIView):
    """
    Manage Gym Profile Settings
    """
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.role != 'GYM_OWNER':
            return Response({"error": "Unauthorized"}, status=403)
        
        user = request.user
        # Assuming 'address' might be on profile or user model directly (MongoEngine)
        # Using getattr safely
        return Response({
            "gym_name": user.gym_name,
            "owner_name": user.name,
            "email": user.email,
            "phone": user.phone,
            "address": getattr(user, 'address', '')
        })

    def put(self, request):
        if request.user.role != 'GYM_OWNER':
            return Response({"error": "Unauthorized"}, status=403)
        
        user = request.user
        data = request.data
        
        if 'gym_name' in data:
            user.gym_name = data['gym_name']
        if 'owner_name' in data:
            user.name = data['owner_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'address' in data:
            user.address = data['address']
            
        user.save()
        return Response({"message": "Profile updated", "gym_name": user.gym_name})

class NotificationView(APIView):
    """
    Handle Notifications (Mock implementation for demo)
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        if request.user.role != 'GYM_OWNER':
             return Response({"error": "Unauthorized"}, status=403)
             
        action = request.data.get('action')
        if action == 'remind_fees':
            # Count pending members
            pending_members = Member.objects(gym_owner=request.user, fees_status='PENDING')
            count = pending_members.count()
            
            # Application Logic: Send SMS/WhatsApp
            # For now, we simulate success
            
            return Response({"message": f"Fee reminders successfully sent to {count} members via WhatsApp.", "count": count})
        
        return Response({"error": "Invalid action"}, status=400)
