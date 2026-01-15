from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, GymOwner
from .authentication import generate_jwt
# import razorpay (Moved to inside method to prevent pkg_resources startup crash)
from django.conf import settings
from datetime import datetime
import mongoengine

class HealthCheckView(APIView):
    def get(self, request):
        try:
            mongoengine.get_db().command('ping')
            return Response({"mongo": "connected", "status": "ok"})
        except Exception as e:
            return Response({"mongo": "error", "message": str(e)}, status=503)

import logging

logger = logging.getLogger(__name__)

class SignupAPIView(APIView):
    def post(self, request):
        try:
            data = request.data
            # ... (rest of logic same as before, simplified for this diff) ...
            email = data.get('email', '').strip().lower()
            password = data.get('password')
            
            # Determine role: Use explicit role or detect via gym_name presence
            role = data.get('role')
            if not role:
                if 'gym_name' in data or 'gym-owner' in request.path:
                    role = 'GYM_OWNER'
                else:
                    role = 'USER'

            if not email or not password:
                return Response({'error': 'Email and password required'}, status=400)

            if role == 'GYM_OWNER':
                if GymOwner.objects(email=email).first():
                    return Response({'error': 'Gym Owner with this email exists'}, status=400)
                user = GymOwner(
                    email=email, 
                    gym_name=data.get('gym_name', 'My Gym'), 
                    role='GYM_OWNER',
                    gym_address=data.get('gym_address', '')
                )
            else:
                username = data.get('username', email.split('@')[0])
                if User.objects(email=email).first() or User.objects(username=username).first():
                    return Response({'error': 'Email or Username already taken'}, status=400)
                user = User(
                    email=email, 
                    username=username, 
                    role='USER',
                    goal=data.get('goal', ''),
                    age=int(data.get('age')) if data.get('age') else None,
                    gender=data.get('gender', '')
                )

            user.set_password(password)
            user.save()

            tokens = generate_jwt(user)
            return Response({
                'user': {'email': user.email, 'role': user.role, 'id': str(user.id)},
                'access': tokens['access'],
                'refresh': tokens['refresh']
            }, status=201)
        except Exception as e:
            logger.error(f"Signup Error: {str(e)}", exc_info=True)
            return Response({'error': 'Internal Server Error. Please contact support.'}, status=500)


class LoginAPIView(APIView):
    def post(self, request):
        identifier = request.data.get('username', '').strip().lower()
        password = request.data.get('password')

        if not identifier or not password:
            return Response({'error': 'Credentials required'}, status=400)

        user = (GymOwner.objects(email=identifier).first() or 
                User.objects(email=identifier).first() or 
                User.objects(username=identifier).first())

        if not user or not user.check_password(password):
            return Response({'error': 'Invalid Credentials'}, status=401)

        tokens = generate_jwt(user)
        
        return Response({
            'user': {
                'email': user.email,
                'role': user.role,
                'id': str(user.id),
                'name': getattr(user, 'gym_name', getattr(user, 'username', 'User')),
                'plan': getattr(user, 'plan_type', 'FREE')
            },
            'access': tokens['access'],
            'refresh': tokens['refresh']
        })

from rest_framework import status, permissions

# ... imports ...

# class ProfileView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         # Debugging User State
#         print(f"DEBUG: ProfileView Accessed. User: {user}, Auth: {user.is_authenticated}")

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # User is guaranteed to be authenticated here
        return Response({
            'email': user.email,
            'role': user.role,
            'id': str(user.id),
            'name': getattr(user, 'gym_name', getattr(user, 'username', 'User')),
            'plan': getattr(user, 'plan_type', 'FREE')
        })

class VerifyPaymentAPIView(APIView):
    def post(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            
            if request.user and request.user.role == 'GYM_OWNER':
                request.user.update_plan('PRO')
                return Response({'status': 'Payment Verified', 'plan': 'PRO'})
            return Response({'error': 'User mismatch'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
