import os
import sys
import django
from pathlib import Path

# --- 1. Environment Setup ---
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / '.env'

def read_env():
    print(f"📂 Loading .env from {ENV_FILE}")
    if not ENV_FILE.exists():
        print("❌ .env file not found!")
        return
    
    with open(ENV_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if '=' in line:
                key, val = line.split('=', 1)
                os.environ[key] = val

read_env()

# --- 2. URI & DNS Diagnostics (PRE-DJANGO) ---
print("\n--- 🔍 DIAGNOZING CONNECTIVITY ---")
uri = os.environ.get('MONGO_URI')
print(f"URI: {uri}")

if not uri:
    print("❌ MONGO_URI missing!")
    # Don't exit yet, let Django try and fail
else:
    # Check for DNS issues specific to +srv
    if "mongodb+srv://" in uri:
        try:
            import dns.resolver
            # Extract hostname
            part = uri.split('@')[1]
            hostname = part.split('/')[0].split('?')[0]
            
            print(f"🔍 Resolving SRV for: _mongodb._tcp.{hostname}")
            try:
                answers = dns.resolver.resolve(f'_mongodb._tcp.{hostname}', 'SRV')
                print(f"✅ DNS Resolution OK. Found {len(answers)} records.")
            except Exception as e:
                print(f"❌ DNS RESOLUTION FAILED: {e}")
                print(f"   👉 CRITICAL: The domain '{hostname}' does not have SRV records.")
                print("   👉 FIX: Your URI is likely missing the unique Cluster ID.")
                print("   👉 EXAMPLE: 'cluster0.gu2la.mongodb.net', NOT just 'fitmitra.mongodb.net'.")
                # We stop here because Django WILL crash
                print("\n⚠️  Stopping execution because DB Connection will definitely fail ⚠️")
                sys.exit(1)
        except ImportError:
            print("⚠️  'dnspython' not installed. Skipping manual DNS check.")

# --- 3. Django Setup ---
print("\n--- ⚙️ LOADING DJANGO ---")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
try:
    django.setup()
    print("✅ Django setup successful.")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

# --- 4. Database Connection Test ---
from mongoengine import get_connection
try:
    # initialize_db already ran during django.setup() -> common.apps.ready()
    # So we just get the connection
    conn = get_connection('default')
    print("🔄 Pinging MongoDB...")
    conn.admin.command('ping')
    print("✅ PING SUCCESSFUL! Database is reachable.")
except Exception as e:
    print(f"❌ CONNECTION FAILED: {e}")

# --- 5. JWT Check ---
print("\n--- 🔐 DIAGNOZING JWT ---")
from django.conf import settings
print(f"SECRET_KEY in Settings: {settings.SECRET_KEY[:5]}...")
if settings.SECRET_KEY != os.getenv('SECRET_KEY'):
    print("⚠️  WARNING: settings.SECRET_KEY does not match .env! Check settings.py generation.")
else:
    print("✅ SECRET_KEY matches.")

print("\n--------------------------")
print("Diagnosis Complete.")
