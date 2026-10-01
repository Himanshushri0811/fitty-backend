import os
import sys
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / '.env')

def test():
    key = os.getenv("GROQ_API_KEY")
    print(f"Key: {key[:10]}...")
    client = Groq(api_key=key)
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hi"}],
            model="llama-3.3-70b-versatile",
        )
        print(f"✅ Groq OK: {completion.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Groq Error: {e}")

if __name__ == "__main__":
    test()
