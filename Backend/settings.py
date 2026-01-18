from pathlib import Path
import os
from datetime import timedelta
from mongo import connect_db

# --------------------------------------------------
# BASE & BOOTSTRAP
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "fitmitra-prod-secret-2024")
DEBUG = os.getenv("DEBUG", "False") == "True"

# --------------------------------------------------
# DATABASE INITIALIZATION (FIRST!)
# --------------------------------------------------
connect_db()

# --------------------------------------------------
# CORE CONFIG
# --------------------------------------------------
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    # Minimal Django services
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    
    # Third-party
    "rest_framework",
    "corsheaders",
    
    # Local Apps
    "accounts",
    "gym_management",
    "ai",
    "explore",
    "social",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
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
# AUTHENTICATION & SECURITY
# --------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.MongoJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
}

CORS_ALLOW_ALL_ORIGINS = True # In production change to specific origins
CORS_ALLOW_CREDENTIALS = True

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

# --------------------------------------------------
# EMAIL CONFIGURATION (SMTP)
# --------------------------------------------------

# STRICTLY use SMTP by default.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False  # Explicitly False for port 587

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "FitMitra Support <fitmitra11@gmail.com>")

print(f"✅ EMAIL SYSTEM: Using SMTP EmailBackend for {EMAIL_HOST_USER} (TLS=True)")
