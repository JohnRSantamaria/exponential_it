from .base import *

import dj_database_url

DEBUG = False
HOST = config("HOST", default="0.0.0.0", cast=str)
# ALLOWED_HOSTS = [f"{HOST}"]
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


MIDDLEWARE.insert(1, "corsheaders.middleware.CorsMiddleware")

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [f"http://{HOST}"]

DATABASES = {"default": dj_database_url.parse(config("DATABASE_PROD"))}

STATIC_URL = "static/"

# Exipiraicon del token
OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": 300,  # 7200s 2 horas, por ejemplo
    "REFRESH_TOKEN_EXPIRATION": 43200,  # 30 Días
}
