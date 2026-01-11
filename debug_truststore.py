
import os
import pymongo
import truststore
import ssl
from dotenv import load_dotenv

# Inject system trust store
truststore.inject_into_ssl()

load_dotenv('.env')
load_dotenv('.env.local')

uri = os.getenv("MONGO_URI")
print("Testing with Truststore injected...")
try:
    # We do NOT pass tlsCAFile because truststore handles it at the socket level
    client = pymongo.MongoClient(uri, tls=True)
    info = client.server_info()
    print("SUCCESS! Version:", info.get('version'))
except Exception as e:
    print("FAILED:", e)
