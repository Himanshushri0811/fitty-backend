import os
import sys
from dotenv import load_dotenv

# Add Backend to path
sys.path.append('d:/demo_project/FITMITRA/Backend')
load_dotenv('d:/demo_project/FITMITRA/Backend/.env')

def test():
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"Testing with Key: {api_key[:10]}...")
        
        if not api_key:
            print("❌ No API Key found in .env")
            return

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents="Say 'Fitty is back!' if you can hear me.",
        )
        print(f"✅ Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test()
