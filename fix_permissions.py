import os
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Ensure AllowAny is imported
    # If IsAuthenticated is imported from rest_framework.permissions, add AllowAny
    if 'from rest_framework.permissions import' in content:
        if 'AllowAny' not in content:
            content = re.sub(
                r'from rest_framework.permissions import (.*)',
                r'from rest_framework.permissions import AllowAny, \1',
                content
            )
    
    # Also handle 'from rest_framework import permissions' style
    # (used in accounts/views.py)
    content = content.replace('permissions.IsAuthenticated', 'permissions.AllowAny')

    # 2. Replace the permission_classes definition
    content = content.replace('[IsAuthenticated]', '[AllowAny]')
    content = content.replace('[IsAuthenticatedOrReadOnly]', '[AllowAny]')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def walk_and_fix(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py') and file != 'fix_permissions.py':
                fix_file(os.path.join(root, file))

if __name__ == "__main__":
    walk_and_fix('d:/demo_project/FITMITRA/Backend')
    print("✅ All permissions set to AllowAny")
