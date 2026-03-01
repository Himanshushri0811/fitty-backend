from pathlib import Path
import os
import sys
from dotenv import load_dotenv
from datetime import timedelta

# --------------------------------------------------
# LOAD ENV
# --------------------------------------------------
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# SECURITY CORE
# --------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "fitmitra-prod-secret-2024")
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "fitmitra-backend.onrender.com",
    ".onrender.com",
]

# --------------------------------------------------
# HTTPS / PROXY (RENDER SAFE)
# --------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = True

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
    "explore",
    "social",
    "diet",
    "workouts",

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
            uuidRepresentation="standard"
        )
        print("✅ MongoDB Connected")
    except Exception as e:
        print("❌ MongoDB Error:", e)
        if not DEBUG:
            sys.exit(1)

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
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://fitty-ai.netlify.app",
]

CORS_ALLOW_CREDENTIALS = False

CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
]

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
# STATIC
# --------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

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