import os
import urllib.parse
from dotenv import load_dotenv

# Load .env explicitly
load_dotenv('.env')

uri = os.getenv("MONGO_URI", "")
print(f"Full URI from env: '{uri}'")

if "@" in uri and "://" in uri:
    try:
        # Manual split to see exactly what is being sent
        scheme, remainder = uri.split("://", 1)
        creds, host = remainder.split("@", 1)
        
        if ":" in creds:
            username, password = creds.split(":", 1)
            print("\n--- CREDENTIALS CHECK ---")
            print(f"Username: '{username}'")
            print(f"Password: '{password}'")
            print(f"Password Length: {len(password)}")
            print(f"Password Bytes: {list(password.encode('utf-8'))}")
            
            if " " in password:
                print("⚠️ WARNING: Spaces detected in password!")
            if "%" in password:
                print("⚠️ WARNING: Percent sign detected. Ensure it's properly encoded if it's part of the password.")
        else:
            print("❌ No password found in URI credential section.")
            
    except Exception as e:
        print(f"❌ Parse Error: {e}")
else:
    print("❌ Invalid URI format in .env")
