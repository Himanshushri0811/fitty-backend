import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_live_chat():
    print("🚀 Starting Live Chat Test...")
    
    # 1. Visitor Send
    print("\n1. Visitor sending message...")
    visitor_id = f"test_vis_{int(time.time())}"
    
    resp = requests.post(f"{BASE_URL}/api/support/live/visitor/", json={
        "visitor_id": visitor_id,
        "message": "Hello, is anyone there?",
        "visitor_name": "Test Visitor"
    })
    
    if resp.status_code != 200:
        print(f"❌ Visitor Send Failed: {resp.text}")
        return
        
    session_id = resp.json().get("session_id")
    print(f"✅ Session Created: {session_id}")
    
    # 2. Agent Poll (Inbox)
    # Login as Gym Owner first
    print("\n2. Agent checking Inbox...")
    ts = int(time.time())
    email = f"test_owner_{ts}@example.com"
    username = f"agent_smith_{ts}"
    
    # Try Login (will fail) -> Signup
    auth_resp = requests.post(f"{BASE_URL}/api/accounts/login/", json={
        "username": email, "password": "password123"
    })
    
    if auth_resp.status_code != 200:
        print("⚠️ Login failed. Creating Agent...")
        signup_resp = requests.post(f"{BASE_URL}/api/accounts/signup/", json={
             "email": email, "password": "password123", "username": username,
             "name": "Agent Smith", "role": "GYM_OWNER", "gym_name": "Matrix Gym"
        })
        if signup_resp.status_code != 201:
             print(f"❌ Signup Failed: {signup_resp.text}")
             return
             
        auth_resp = requests.post(f"{BASE_URL}/api/accounts/login/", json={
            "username": email, "password": "password123"
        })
        
    if auth_resp.status_code != 200:
        print(f"❌ Login Failed: {auth_resp.text}")
        return
        
    token = auth_resp.json().get("access")
    headers = {"Authorization": f"Bearer {token}"}
    
    inbox_resp = requests.get(f"{BASE_URL}/api/support/live/agent/", headers=headers)
    if inbox_resp.status_code != 200:
        print(f"❌ Inbox Fetch Failed: {inbox_resp.text}")
        return
        
    sessions = inbox_resp.json()
    my_session = next((s for s in sessions if s['id'] == session_id), None)
    
    if my_session:
        print(f"✅ Found Session in Inbox from {my_session['visitor_name']}")
    else:
        print("❌ Session not found in Inbox")
        return

    # 3. Agent Reply
    print("\n3. Agent replying...")
    reply_resp = requests.post(f"{BASE_URL}/api/support/live/agent/", headers=headers, json={
        "session_id": session_id,
        "message": "Yes, I am here! How can I help?"
    })
    
    if reply_resp.status_code != 200:
        print(f"❌ Agent Reply Failed: {reply_resp.text}")
        return
    print("✅ Agent Reply Sent.")
    
    # 4. Visitor Poll
    print("\n4. Visitor checking for reply...")
    poll_resp = requests.get(f"{BASE_URL}/api/support/live/visitor/?visitor_id={visitor_id}")
    messages = poll_resp.json().get("messages", [])
    
    last_msg = messages[-1]
    if last_msg['sender'] == 'agent':
        print(f"✅ Visitor received reply: {last_msg['content']}")
    else:
        print("❌ Visitor did not receive reply.")
        
    print("\n🎉 Live Chat Test Complete!")

if __name__ == "__main__":
    test_live_chat()
