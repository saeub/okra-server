# flake8: noqa
import os
from pathlib import Path

from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure_key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if os.getenv("API_HOST"):
    ALLOWED_HOSTS = [os.getenv("API_HOST")]
else:
    ALLOWED_HOSTS = []

if os.getenv("OKRA_URL"):
    CORS_ALLOWED_ORIGINS = [
        os.getenv("OKRA_URL"),
    ]
else:
    CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "X-Participant-ID",
    "X-Device-Key",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "okra_server",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "okra_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "okra_server.views.api_info",
            ],
        },
    },
]

WSGI_APPLICATION = "okra_server.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
LOGIN_URL = "/login"
FORCE_SCRIPT_NAME = os.getenv("FORCE_SCRIPT_NAME")
if FORCE_SCRIPT_NAME is not None:
    STATIC_URL = FORCE_SCRIPT_NAME + STATIC_URL
    LOGIN_URL = FORCE_SCRIPT_NAME + LOGIN_URL

STATIC_ROOT = BASE_DIR / "staticfiles"

API_INFO = {
    "name": os.getenv("API_NAME", "Development API"),
    "icon_url": os.getenv("API_ICON_URL"),
}
