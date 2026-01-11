
import os
import pymongo
import certifi
from dotenv import load_dotenv

# Load env variables from up one level or current level
load_dotenv('.env')
load_dotenv('.env.local')

uri = os.getenv("MONGO_URI")
if not uri:
    print("MONGO_URI not found!")
    exit(1)

print(f"Testing connection...")

# TEST 1: Certifi
print("\n--- TEST 1: using certifi ---")
try:
    client = pymongo.MongoClient(
        uri, 
        tlsCAFile=certifi.where(),
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000
    )
    info = client.server_info()
    print("SUCCESS! Server version:", info.get('version'))
except Exception as e:
    print("FAILED:", e)

# TEST 2: Insecure
print("\n--- TEST 2: tlsAllowInvalidCertificates=True ---")
try:
    client = pymongo.MongoClient(
        uri, 
        tls=True,
        tlsAllowInvalidCertificates=True,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000
    )
    info = client.server_info()
    print("SUCCESS! Server version:", info.get('version'))
except Exception as e:
    print("FAILED:", e)
