
import os

search_string = "ObjectIdField"
exclude_dirs = ["migrations", "__pycache__", "venv", ".git"]

print(f"Searching for '{search_string}' in .py files...")

for root, dirs, files in os.walk("."):
    # Exclude directories
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if search_string in line:
                            print(f"FOUND in {path}:{i+1}")
                            print(f"   Line: {line.strip()}")
            except Exception as e:
                print(f"Error reading {path}: {e}")

print("Search complete.")
