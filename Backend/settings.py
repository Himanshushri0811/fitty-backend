from pathlib import Path
import os
from datetime import timedelta

# --------------------------------------------------
# BASE & BOOTSTRAP
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "fitmitra-prod-secret-2024")
DEBUG = os.getenv("DEBUG", "False") == "True"

# Production Security & Proxy Configuration (Render)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = False  # Render handles SSL termination

# --------------------------------------------------
# CORE CONFIG
# --------------------------------------------------
# --------------------------------------------------
# CORE CONFIG
# --------------------------------------------------
ALLOWED_HOSTS = ["*"] # Allow all for Render dynamic IPs/Domains

INSTALLED_APPS = [
    # Minimal Django services
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    
    # Third-party
    "rest_framework",
    "corsheaders",
    
    # Local Apps
    "common",  # Core app first for database init
    "accounts",
    "gym_management",
    "ai",
    "explore",
    "social",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware", # CORS FIRST
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    # Note: Sessions and default Auth middleware removed for Pure NoSQL JWT
]

# --------------------------------------------------
# PURE NOSQL ENFORCEMENT
# --------------------------------------------------
# Dummy default to satisfy Django core, but no SQL table will ever be created.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy', 
    }
}

# --------------------------------------------------
# MONGOENGINE CONNECTION (Production-Grade)
# --------------------------------------------------
import mongoengine
import sys

_MONGO_URI = os.getenv("MONGO_URI")

if not _MONGO_URI:
    # Fail hard if DB is not configured
    print("❌ CRITICAL: MONGO_URI is missing from environment variables.")
    if os.getenv("DJANGO_ENV") == "production":
        sys.exit(1)
elif "test" not in sys.argv: # Avoid connecting during test runner setup if separate
    try:
        mongoengine.connect(
            host=_MONGO_URI, 
            alias='default', 
            uuidRepresentation='standard'
        )
        print("✅ MongoEngine: Registered default connection.")
    except Exception as e:
        print(f"❌ MongoEngine Connection Error: {e}")
        # In production, we can't run without DB
        if not DEBUG:
            sys.exit(1)

# --------------------------------------------------
# AUTHENTICATION & SECURITY
# --------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'accounts.authentication.MongoJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny', # Default open, secure specific views
    ),
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "https://fitmitra.onrender.com").split(",")
    CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "https://fitmitra.onrender.com").split(",")

# --------------------------------------------------
# URLS & WSGI
# --------------------------------------------------
ROOT_URLCONF = "Backend.urls"
WSGI_APPLICATION = "Backend.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

# --------------------------------------------------
# STORAGE
# --------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# EXTRA SETTINGS
# --------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = False
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Payment Integration (Razorpay)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
