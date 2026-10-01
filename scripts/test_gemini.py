import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / '.env')

def test():
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ No API Key found in .env")
            return

        model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        print(f"Testing model: {model}")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents="Say 'Fitty is back!' if you can hear me.",
        )
        print(f"✅ Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test()