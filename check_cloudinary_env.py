import os
from dotenv import load_dotenv
import cloudinary

# Load .env
load_dotenv(override=True)

cloud_name = os.getenv('CLOUD_NAME')
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

print(f"DEBUG CHECK:")
print(f"CLOUD_NAME: '{cloud_name}'")
print(f"API_KEY: '{api_key}'") 
print(f"API_SECRET: '{api_secret}'")

if not cloud_name or "cloudinary://" in cloud_name:
    print("❌ ERROR: CLOUD_NAME is seemingly incorrect or the full URL.")
else:
    print("✅ CLOUD_NAME format looks correct.")

# Try a dummy config
try:
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
    print("✅ Cloudinary config call succeeded.")
except Exception as e:
    print(f"❌ Cloudinary config call failed: {e}")
