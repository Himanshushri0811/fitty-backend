import os
import django
from mongoengine.connection import _get_db

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from accounts.models import User, GymOwner

def wipe_users():
    print("⚠️  STARTING DATABASE FLUSH (Users & GymOwners)...")
    
    try:
        user_count = User.objects.count()
        gym_owner_count = GymOwner.objects.count()
        
        print(f"   Found {user_count} Users and {gym_owner_count} Gym Owners.")

        # Delete all
        User.objects.delete()
        GymOwner.objects.delete()
        
        print("✅  SUCCESS: All User and GymOwner records have been permanently deleted.")
        print("   You can now sign up with any username/email.")
        
    except Exception as e:
        print(f"❌  ERROR: {e}")

if __name__ == "__main__":
    wipe_users()
