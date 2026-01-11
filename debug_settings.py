import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
try:
    django.setup()
    print("Django setup successful")
except Exception as e:
    import traceback
    traceback.print_exc()
