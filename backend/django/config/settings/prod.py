from .base import *

import dj_database_url

DEBUG = False
HOST = config("HOST", default="0.0.0.0", cast=str)
ALLOWED_HOSTS = [f"{HOST}"]

# Application definition
THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "oauth2_provider",
]

USER_APPS = [
    "applications.authentication.users",
    "applications.authentication.services",
]
INSTALLED_APPS += THIRD_PARTY_APPS + USER_APPS

MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")

# Rest framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# Modelo para la autenticacion
AUTH_USER_MODEL = "users.User"

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [f"http://{HOST}"]

DATABASES = {"default": dj_database_url.parse(config("DATABASE_PROD"))}

STATIC_URL = "static/"

# Exipiraicon del token
OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": 36000,  # 7200s 2 horas, por ejemplo
}
