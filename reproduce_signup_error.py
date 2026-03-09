import os
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from accounts.models import User

def test_signup_logic():
    print("Testing User creation with string DOB...")
    try:
        # Cleanup existing test user
        User.objects(email="test_debug@example.com").delete()
        
        user = User(
            email="test_debug@example.com",
            username="test_debug",
            role="USER",
            name="Test Debug"
        )
        user.set_password("password123")
        
        # This is what SignupAPIView does:
        user.dob = "1990-01-01" 
        
        print("Attempting to save user...")
        user.save()
        print(f"✅ User saved successfully. ID: {user.id}")
        
        from accounts.authentication import generate_jwt
        print("Attempting to generate JWT...")
        tokens = generate_jwt(user)
        print("✅ JWT generated successfully")
        print(f"Access Token: {tokens['access'][:20]}...")
        
    except Exception as e:
        print(f"❌ Operation failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_signup_logic()
