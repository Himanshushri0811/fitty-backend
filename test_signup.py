import requests
import json

url = "http://127.0.0.1:8000/api/accounts/signup/"
payload = {
    "email": "testuser_v3@example.com",
    "password": "Test@123",
    "username": "testuser_v3",
    "role": "USER",
    "age": "25",
    "gender": "Male",
    "goal": "Weight Loss"
}
headers = {
    'Content-Type': 'application/json'
}

try:
    print(f"Sending POST to {url}...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code != 201:
        print("Error Response First 1000 chars:")
        print(response.text[:1000])
    else:
        print("Success!")
        print(response.json())
except Exception as e:
    print(f"Request Failed: {e}")
