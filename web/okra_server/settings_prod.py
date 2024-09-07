"""Settings for production environment."""

import os

from okra_server.settings import *  # noqa: F403, F401

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.getenv("POSTGRES_HOST"),
        "NAME": os.getenv("POSTGRES_DB_NAME"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    }
}

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
