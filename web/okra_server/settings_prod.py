"""Settings for production environment."""

import os

from okra_server.settings import *  # noqa: F403, F401

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "postgres",
        "NAME": "okra_server",
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    }
}
