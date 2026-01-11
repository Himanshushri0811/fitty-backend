
import os
import pymongo
import certifi
from dotenv import load_dotenv

load_dotenv('.env')
load_dotenv('.env.local')

uri = os.getenv("MONGO_URI")
print("Testing with Pymongo 4 + Certifi...")
try:
    client = pymongo.MongoClient(uri, tlsCAFile=certifi.where())
    info = client.server_info()
    print("SUCCESS! Version:", info.get('version'))
except Exception as e:
    print("FAILED:", e)
