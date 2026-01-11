import os
from dotenv import load_dotenv
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Load .env BEFORE anything else
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')

application = get_wsgi_application()
