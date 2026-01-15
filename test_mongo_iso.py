import os
from pymongo import MongoClient
import urllib.parse

# Original URI from .env
username = "hshrivastava1108_db_user"
password = "FitMitra_DBu63gu"
cluster = "cluster0.wdu63gu.mongodb.net"
dbname = "fitmitra"

# 1. Try exact URI from .env
uri_original = "mongodb+srv://hshrivastava1108_db_user:FitMitra_DBu63gu@cluster0.wdu63gu.mongodb.net/fitmitra?retryWrites=true&w=majority&appName=Cluster0"

# 2. Try simplified URI
uri_simple = "mongodb+srv://hshrivastava1108_db_user:FitMitra_DBu63gu@cluster0.wdu63gu.mongodb.net/?retryWrites=true&w=majority"

def test_conn(uri, name):
    print(f"\n--- Testing {name} ---")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Force a call
        client.admin.command('ping')
        print(f"✅ {name} SUCCESS")
        return True
    except Exception as e:
        print(f"❌ {name} FAILED: {e}")
        return False

# Run tests
test_conn(uri_original, "Original URI")
test_conn(uri_simple, "Simplified URI (no db/appName)")
