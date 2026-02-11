from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # Auto-create Admin User on startup if not exists
        # This runs on server start. Ensure DB is ready.
        # MongoEngine connection is in settings.py, which runs before this.
        import os
        from django.conf import settings
        
        # Avoid running in autoreload main process double execution (simple check)
        if os.environ.get('RUN_MAIN', None) != 'true':
            # This logic might run twice in dev mode without this check, but it's idempotent.
            pass

        try:
            # Import model inside method to ensure registry is ready
            from .models import User
            
            admin_email = os.getenv("ADMIN_EMAIL", "anshu@fitty.com")
            admin_pass = os.getenv("ADMIN_PASSWORD", "admin@4321")
            
            # Check if admin exists
            existing_admin = User.objects(email=admin_email).first()
            
            if not existing_admin:
                print(f"🛠️ Creating Default Admin User: {admin_email}")
                admin_user = User(
                    email=admin_email,
                    username="admin", 
                    role='ADMIN',
                    name="System Admin",
                    is_active=True
                )
                admin_user.set_password(admin_pass)
                admin_user.save()
                print("✅ Default Admin Created Successfully.")
            else:
                # Optional: Ensure role is ADMIN if email matches?
                if existing_admin.role != 'ADMIN':
                    print(f"⚠️ User {admin_email} exists but is not ADMIN. Promoting...")
                    existing_admin.role = 'ADMIN'
                    existing_admin.save()
                    print("✅ User Promoted to ADMIN.")
                    
        except ImportError:
            pass # Models not ready yet or specific context issues
        except Exception as e:
            # In some startup contexts (like migrate), DB might not be reachable yet or connection fails
            # We catch to avoid breaking startup
            print(f"⚠️ Autosetup Admin Warning: {e}")
