# config\settings\local.py
from .base import *

import dj_database_url

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]


MIDDLEWARE.insert(1, "corsheaders.middleware.CorsMiddleware")


# Rest framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}


CORS_ALLOW_ALL_ORIGINS = True

DATABASES = {"default": dj_database_url.parse(config("DATABASE_LOCAL"))}


STATIC_URL = "static/"

# Exipiraicon del token
OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": 36000,  # 7200s 2 horas, por ejemplo
}
