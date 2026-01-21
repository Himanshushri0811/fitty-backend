import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import authentication, exceptions
from accounts.models import User, GymOwner
from bson.objectid import ObjectId

class MongoJWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT Auth using MongoEngine Users
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except (IndexError, jwt.DecodeError):
            raise exceptions.AuthenticationFailed('Invalid token')

        user_id = payload.get('user_id')
        role = payload.get('role')

        if not user_id or not role:
            raise exceptions.AuthenticationFailed('Invalid token payload')

        user = None
        try:
            if role == 'GYM_OWNER':
                user = GymOwner.objects(id=user_id).first()
            else:
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
