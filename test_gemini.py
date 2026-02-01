import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load Environment Manually
print("--- DIGNOSTIC REPORT ---")
print(f"Current Working Directory: {os.getcwd()}")
env_path = os.path.join(os.getcwd(), '.env')
print(f"Loading .env from: {env_path}")

if os.path.exists(env_path):
    print("✅ .env file found.")
    with open(env_path, 'r') as f:
        print(f"📄 Raw File Content:\n{f.read()}")
    load_dotenv(env_path, override=True) # Force reload
else:
    print("❌ .env file NOT found!")

# 2. Check Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try alternate name just in case
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("⚠️ GEMINI_API_KEY missing, using GOOGLE_API_KEY instead.")
    else:
        print("❌ CRITICAL: No API Key found in environment.")
        exit(1)

# Mask Key for safety
print(f"🔑 Raw Key from Env: {repr(api_key)}")

# Check for hidden whitespace
if api_key.strip() != api_key:
    print("❌ WARNING: Key has leading/trailing whitespace! trimming it...")
    api_key = api_key.strip()

# 3. Test API
print("\n--- TESTING GEMINI API (Env Key) ---")
try:
    genai.configure(api_key=api_key)
    # Using specific model from list
    model = genai.GenerativeModel('models/gemini-2.0-flash')
    response = model.generate_content("Test")
    print(f"✅ SUCCESS with Env Key! Response: {response.text}")
except Exception as e:
    print(f"❌ FAILURE with Env Key: {e}")
    
    # 4. Fallback Test
    print("\n--- TESTING HARDCODED KEY (Double Check) ---")
    hardcoded = "AIzaSyBjgmyMKIFwReydfTXCYYaclkoXxpv8Kbo"
    print(f"Testing Key: {hardcoded}")
    try:
        genai.configure(api_key=hardcoded)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Test")
        print(f"✅ SUCCESS with Hardcoded Key! Response: {response.text}")
    except Exception as e:
        print(f"❌ FAILURE with Hardcoded Key: {e}")
