import requests
import os
import django
import sys

# Setup Django Environment (for standalone script if needed, but requests is better for API testing)
# We will use purely HTTP requests against the running server

BASE_URL = "http://127.0.0.1:8000"

def test_fitty_flow():
    print("🚀 Starting Fitty API Test...")
    
    # 1. Login/Signup
    # We need a valid token. Let's try to login as a known user or create one.
    import time
    timestamp = int(time.time())
    email = f"test_fitty_{timestamp}@example.com"
    username = f"testfittyuser_{timestamp}"
    password = "password123"
    
    auth_url = f"{BASE_URL}/api/accounts/login/"
    signup_url = f"{BASE_URL}/api/accounts/signup/"
    
    session = requests.Session()
    
    # Try Login
    print(f"🔑 Logging in as {email}...")
    resp = session.post(auth_url, json={"email": email, "password": password})
    
    if resp.status_code != 200:
        print("⚠️ Login failed. Trying to Signup...")
        resp = session.post(signup_url, json={
            "email": email, 
            "password": password, 
            "name": "Test User",
            "role": "USER",
            "username": username
        })
        if resp.status_code != 201:
            print(f"❌ Signup Failed: {resp.text}")
            return
    
    tokens = resp.json()
    access_token = tokens.get('access')
    if not access_token:
        print("❌ No access token received.")
        return
        
    print("✅ Login Successful.")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Send First Message
    chat_url = f"{BASE_URL}/api/ai/chat/"
    print("\n💬 Sending First Message: 'Hello Fitty, I want to build muscle.'")
    resp = session.post(chat_url, headers=headers, json={"message": "Hello Fitty, I want to build muscle."})
    
    if resp.status_code != 200:
        print(f"❌ Message Failed: {resp.text}")
        return
        
    data = resp.json()
    reply = data.get("reply")
    session_id = data.get("session_id")
    
    print(f"🤖 User: Hello Fitty...")
    print(f"🤖 Fitty: {reply[:100]}...")
    print(f"🆔 Session ID: {session_id}")
    
    if not session_id:
        print("❌ Session ID missing.")
        return
        
    # 3. Send Follow-up (Context Test)
    print("\n💬 Sending Follow-up: 'What should I eat for breakfast?'")
    resp = session.post(chat_url, headers=headers, json={
        "message": "What should I eat for breakfast?",
        "session_id": session_id
    })
    
    if resp.status_code != 200:
        print(f"❌ Follow-up Failed: {resp.text}")
        return
        
    data = resp.json()
    reply = data.get("reply")
    
    print(f"🤖 User: What should I eat...")
    print(f"🤖 Fitty: {reply[:100]}...")
    
    # Verify Session ID remains same
    if data.get("session_id") != session_id:
        print(f"⚠️ Warning: Session ID changed! Expected {session_id}, got {data.get('session_id')}")
        
    # 4. Check History
    print("\n📜 Fetching Chat History...")
    resp = session.get(chat_url, headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ History Fetch Failed: {resp.text}")
        return
        
    history = resp.json().get("history", [])
    print(f"✅ History Count: {len(history)} messages")
    
    if len(history) >= 4: # User, Bot, User, Bot
        print("✅ History integrity verified.")
    else:
        print("⚠️ History count mismatch.")

    print("\n🎉 Test Complete!")

if __name__ == "__main__":
    test_fitty_flow()
