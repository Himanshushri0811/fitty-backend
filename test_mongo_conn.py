import os
import ssl
import sys
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

def test_connection():
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("Error: MONGO_URI not found in .env file")
        return

    print(f"Testing connection to: {uri[:20]}...")

    # Method 1: Standard Connection
    print("\n--- Method 1: Standard Atlas Connection ---")
    try:
        client = MongoClient(
            uri,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        print("Result: SUCCESS")
    except Exception as e:
        print(f"Result: FAILED - {e}")

    # Method 2: Connection with TLS Bypass (Insecure)
    print("\n--- Method 2: TLS Bypass (Insecure) ---")
    try:
        client = MongoClient(
            uri,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        print("Result: SUCCESS")
    except Exception as e:
        print(f"Result: FAILED - {e}")

    # Method 3: Legacy SSL Style (PyMongo 3.x style compatible)
    print("\n--- Method 3: Legacy Connection Style ---")
    try:
        client = MongoClient(
            uri,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        print("Result: SUCCESS")
    except Exception as e:
        print(f"Result: FAILED - {e}")

    print("\n--- TROUBLESHOOTING STEPS ---")
    print("If all methods failed with 'SSL: TLSV1_ALERT_INTERNAL_ERROR':")
    print("1. Go to https://cloud.mongodb.com/")
    print("2. Navigate to 'Network Access'")
    print("3. Add '0.0.0.0/0' temporarily to see if it's an IP whitelist issue.")
    print("4. Ensure your password doesn't contain special characters like '@' or ':' without being URI encoded.")

if __name__ == "__main__":
    test_connection()
