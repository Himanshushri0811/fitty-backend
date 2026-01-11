import jwt
from datetime import datetime, timedelta
secret = "test_secret"
payload = {"user_id": "123", "exp": datetime.utcnow() + timedelta(days=1)}
token = jwt.encode(payload, secret, algorithm="HS256")
print(f"Token type: {type(token)}")
print(f"Token: {token}")
decoded = jwt.decode(token, secret, algorithms=["HS256"])
print(f"Decoded: {decoded}")
