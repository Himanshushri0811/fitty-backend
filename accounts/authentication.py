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
        if not auth_header:
            return None

        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.InvalidSignatureError:
            # Important: Log this to see if keys mismatch
            print(f"DEBUG: JWT Signature verification failed. Key used: {settings.SECRET_KEY[:5]}...")
            raise exceptions.AuthenticationFailed('Invalid token signature')
        except (IndexError, jwt.DecodeError) as e:
            print(f"DEBUG: JWT Decode Error: {e}")
            raise exceptions.AuthenticationFailed('Invalid token')

        user_id = payload.get('user_id')
        role = payload.get('role')

        if not user_id:
            raise exceptions.AuthenticationFailed('Invalid token payload')

        user = None
        try:
            user = User.objects(id=user_id).first()
        except:
             raise exceptions.AuthenticationFailed('Invalid User ID')

        if not user:
            raise exceptions.AuthenticationFailed('User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User is inactive')

        return (user, None)

def generate_jwt(user):
    """
    Generate Access & Refresh tokens
    """
    role = user.role
    
    access_payload = {
        'user_id': str(user.id),
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow()
    }
    
    refresh_payload = {
        'user_id': str(user.id),
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
    
    return {
        'access': access_token,
        'refresh': refresh_token
    }
