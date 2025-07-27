# config\settings\prod.py
import os
import dj_database_url

from .base import *
from decouple import Csv

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

HOST = config("HOST", default="15.236.59.110,15.188.6.72,admin-django", cast=Csv())
ALLOWED_HOSTS = HOST


CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [f"http://{h}" for h in HOST]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {"default": dj_database_url.parse(config("DATABASE_PROD"))}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
