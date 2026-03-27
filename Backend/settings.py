from pathlib import Path
import os
import sys
import logging
from dotenv import load_dotenv
from datetime import timedelta

# --------------------------------------------------
# LOAD ENV
# --------------------------------------------------
load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# SECURITY CORE
# --------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fitmitra-fallback-key-2024")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "fitmitra-backend.onrender.com",
    ".onrender.com",
    "fitmitra.onrender.com",
]

# --------------------------------------------------
# HTTPS / PROXY (RENDER SAFE)
# --------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = not DEBUG # Disable for local testing

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# --------------------------------------------------
# APPS
# --------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    "common",
    "accounts",
    "gym_management",
    "ai",
    "missions",
    "social",
    "diet",
    "workouts",
    "fitty_ai",

    "cloudinary",
    "cloudinary_storage",
]

# --------------------------------------------------
# MIDDLEWARE (JWT ONLY – NO CSRF)
# --------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# --------------------------------------------------
# DATABASE (NO SQL – PURE MONGO)
# --------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.dummy",
    }
}

# --------------------------------------------------
# MONGOENGINE CONNECTION
# --------------------------------------------------
import mongoengine

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ MONGO_URI missing")
    if not DEBUG:
        sys.exit(1)

if "test" not in sys.argv:
    try:
        mongoengine.connect(
            host=MONGO_URI,
            alias="default",
            uuidRepresentation="standard",
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000
        )
        print("✅ MongoDB Connected Successfully")
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        # In production, we don't exit(1) immediately to allow health checks
        # and logs to be visible on Render. Instead, we log the failure.
        logger = logging.getLogger(__name__)
        logger.critical(f"FATAL: Could not connect to MongoDB: {e}")

# --------------------------------------------------
# REST FRAMEWORK (JWT AUTH)
# --------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.MongoJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
}

# --------------------------------------------------
# CORS (NETLIFY → RENDER)
# --------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

# --------------------------------------------------
# CLOUDINARY
# --------------------------------------------------
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUD_NAME"),
    "API_KEY": os.getenv("API_KEY"),
    "API_SECRET": os.getenv("API_SECRET"),
}

import cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    secure=True
)

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# --------------------------------------------------
# RAZORPAY / GEMINI (MISSING IN ORIGINAL)
# --------------------------------------------------
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# --------------------------------------------------
# STATIC / WHITENOISE
# --------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_MANIFEST_STRICT = False  # Prevent 500 if static file missing
WHITENOISE_USE_FINDERS = True

# --------------------------------------------------
# URL / WSGI
# --------------------------------------------------
ROOT_URLCONF = "Backend.urls"
WSGI_APPLICATION = "Backend.wsgi.application"

# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

# --------------------------------------------------
# LOGGING (REVEAL PROD ERRORS)
# --------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# --------------------------------------------------
# GLOBAL
# --------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = False
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# EMAIL (SMTP)
# --------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = "Fitty Support <fitmitra11@gmail.com>"