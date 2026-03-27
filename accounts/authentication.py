import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import authentication, exceptions
from accounts.models import User
from bson.objectid import ObjectId

class MongoJWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT Auth using MongoEngine Users
    """
    def authenticate(self, request):
        # Support both standard styles
        auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
        
        # --------------------------------------------------
        # HACKATHON FAILSAFE: GLOBAL AUTO-AUTH
        # If no token is provided, or token is invalid, 
        # return the Demo User automatically!
        # --------------------------------------------------
        demo_user_id = "65e000000000000000000000"
        try:
             from .models import User
             mock_user = User.objects(id=demo_user_id).first()
             if not mock_user:
                 mock_user = User(
                     id=ObjectId(demo_user_id),
                     email="test@test.com",
                     role="USER", 
                     name="Demo Champ",
                     username="demochamp"
                 )
        except Exception:
             mock_user = None # Will fallback to Anonymous if really broken

        if not auth_header:
            # NO TOKEN? => Return Demo User (Success for Hackathon)
            return (mock_user, None) if mock_user else None

        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except Exception as e:
            # INVALID TOKEN? => Return Demo User (Stable for Hackathon)
            print(f"DEBUG: Auth Failed ({e}), falling back to Demo User.")
            return (mock_user, None) if mock_user else None

        user_id = payload.get('user_id')
        role = payload.get('role')

        if user_id == demo_user_id:
             return (mock_user, None) if mock_user else None

        user = None
        try:
            user = User.objects(id=user_id).first()
        except:
             return (mock_user, None) if mock_user else None

        if not user or not user.is_active:
            return (mock_user, None) if mock_user else None

        return (user, None)

        return (user, None)

def generate_jwt(user=None, user_id=None, role=None):
    """
    Generate Access & Refresh tokens from a User object OR raw ID/Role
    """
    u_id = str(user.id) if user else str(user_id)
    u_role = user.role if user else role
    
    access_payload = {
        'user_id': u_id,
        'role': u_role,
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow()
    }
    
    refresh_payload = {
        'user_id': u_id,
        'role': u_role,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
    
    return {
        'access': access_token,
        'refresh': refresh_token
    }
