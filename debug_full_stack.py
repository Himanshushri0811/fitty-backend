
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# 0. Load Env explicitly (simulate manage.py)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

import django
from mongoengine import connect, disconnect

# 1. Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Backend.settings")
django.setup()

# 2. Imports after setup
from accounts.models import User
from accounts.authentication import generate_jwt
import mongoengine

print("\n--- DEBUG START ---")

# 3. Check Connection
try:
    db = mongoengine.get_connection('default')
    print("✅ Connection Object Found")
    db.admin.command('ping')
    print("✅ Ping Success")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    sys.exit(1)

# 4. Test User Creation
email = "debug_user_v8@example.com"
print(f"Attempting to create user: {email}")

try:
    # Cleanup if exists
    User.objects(email=email).delete()
    
    user = User(
        email=email,
        username="debug_user_v8",
        role="USER",
        password="hashed_password_simulation" 
    )
    user.save()
    print(f"✅ User Saved with ID: {user.id}")
    
    # 5. Test JWT Generation
    tokens = generate_jwt(user)
    print(f"✅ JWT Generated: {tokens['access'][:20]}...")

except Exception as e:
    print("❌ ERROR OCCURRED during operation:")
    import traceback
    traceback.print_exc()

print("--- DEBUG END ---")
