# config\settings\prod.py
import os
import dj_database_url

from .base import *
from decouple import Csv

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

HOST = config("HOST", default="", cast=Csv())
ALLOWED_HOSTS = HOST

CORS_ALLOW_CREDENTIALS = False
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]


CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {"default": dj_database_url.parse(config("DATABASE_LOCAL"))}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"
