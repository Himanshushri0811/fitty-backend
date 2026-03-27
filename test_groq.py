import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv('d:/demo_project/FITMITRA/Backend/.env')

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
