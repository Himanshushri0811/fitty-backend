from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.conf import settings
import razorpay
import hmac
import hashlib
import json
from .models import PaymentLog
from .service import SubscriptionService

class CreateSubscriptionOrderView(APIView):
    """
    Creates a Razorpay Order for Pro Plan Upgrade.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        if request.user.role != 'GYM_OWNER':
            return Response({"error": "Only Gym Owners can subscribe"}, status=403)

        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            print("❌ Razorpay Keys Error: Keys are missing in settings.")
            return Response({"error": "Payment Gateway Configuration Missing"}, status=500)

        if "YOUR_RAZORPAY" in settings.RAZORPAY_KEY_ID:
             print("❌ Razorpay Keys Error: Placeholder values detected.")
             return Response({"error": "Payment Gateway keys not configured"}, status=500)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # PRO Plan is fixed at 299 INR for now
        amount_paise = 299 * 100 
        currency = "INR"
        
        try:
            order_data = {
                "amount": amount_paise,
                "currency": currency,
                "receipt": f"rcpt_{request.user.id}_{int(request.user.created_at.timestamp())}",
                "notes": {
                    "gym_owner_id": str(request.user.id),
                    "plan": "PRO_MONTHLY"
                }
            }
            order = client.order.create(data=order_data)
            
            # Log the attempt
            PaymentLog(
                gym_owner=request.user,
                razorpay_order_id=order['id'],
                amount=299.00,
                status='created',
                payload_dump=order
            ).save()
            
            return Response({
                "order_id": order['id'],
                "amount": order['amount'],
                "currency": order['currency'],
                "key_id": settings.RAZORPAY_KEY_ID,
                "plan": "PRO_MONTHLY"
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class VerifySubscriptionView(APIView):
    """
    Verifies Razorpay Signature and Activates Pro Plan.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
            return Response({"error": "Missing payment details"}, status=400)
            
        # Verify Signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        try:
            # Razorpay SDK verification
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params_dict)
            
            # If successful, activate plan
            SubscriptionService.activate_pro_plan(request.user)
            
            # Log success
            PaymentLog(
                gym_owner=request.user,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
                amount=299.00,
                status='success'
            ).save()
            
            return Response({"status": "active", "message": "Pro Plan Activated Successfully!"})
            
        except razorpay.errors.SignatureVerificationError:
            return Response({"error": "Payment Signature Verification Failed"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class RazorpayWebhookView(APIView):
    """
    Handle async payment events (optional but recommended).
    """
    def post(self, request):
        # Todo: Implement webhook signature verification and handling
        return Response({"status": "received"})
