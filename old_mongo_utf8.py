import os
import sys
import certifi
import mongoengine
from dotenv import load_dotenv
from pathlib import Path

# Load .env variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

def connect_db():
    """
    Production-ready logic to connect to MongoDB Atlas
    Handles SSL/TLS issues for Python 3.12 on Windows
    """
    mongo_uri = os.getenv("MONGO_URI")
    
    if not mongo_uri:
        print("CRITICAL: MONGO_URI missing from environment")
        sys.exit(1)

    print(f"INFO: Connecting to Atlas: {mongo_uri[:25]}...")

    try:
        # Simplified check for existing connection
        try:
            mongoengine.get_connection()
            return True
        except:
            pass

        # Configuration for MongoDB Atlas connection
        # Optimized for Python 3.12 + certifi for Windows SSL Store issues
        connect_args = {
            'host': mongo_uri,
            'tls': True,
            'tlsCAFile': certifi.where(),
            'serverSelectionTimeoutMS': 15000,
            'connectTimeoutMS': 15000,
            'retryWrites': True,
            'w': 'majority',
            'alias': 'default',
        }

        # DEV ONLY: Toggle this via .env if you are behind a corporate proxy/firewall
        if os.getenv("MONGO_TLS_INSECURE") == "True":
            print("WARNING: Using Insecure TLS Bypass (MONGO_TLS_INSECURE=True)")
            connect_args['tlsAllowInvalidCertificates'] = True
            connect_args['tlsAllowInvalidHostnames'] = True

        # Establish global connection via MongoEngine
        mongoengine.connect(**connect_args)
        
        # Immediate validation via ping
        mongoengine.get_db().command('ping')
        print("SUCCESS: MongoDB Atlas connection established.")
        return True

    except Exception as e:
        print(f"FATAL ERROR: Could not connect to Atlas: {str(e)}")
        
        # Diagnostic for the common Handshake error
        if "TLSV1_ALERT_INTERNAL_ERROR" in str(e):
            print("\n--- ACTION REQUIRED: ATLAS IP WHITELIST ---")
            print("The error 'TLSV1_ALERT_INTERNAL_ERROR' usually means Atlas rejected your IP.")
            print("1. Log in to: https://cloud.mongodb.com/")
            print("2. Go to 'Network Access' -> 'Add IP Address'.")
            print("3. Add '0.0.0.0/0' (Allow Access from Anywhere) to test.")
        
        sys.exit(1)

if __name__ == "__main__":
    connect_db()
