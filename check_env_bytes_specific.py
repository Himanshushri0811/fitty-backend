
with open('.env', 'rb') as f:
    for line in f:
        if b'MONGO_URI' in line:
            print(f"MONGO_URI line repr: {repr(line)}")
