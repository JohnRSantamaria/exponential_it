# config\settings\local.py
import os
import dj_database_url

from .base import *
from decouple import config, Csv

DEBUG = True

ENVIRONMENT: str = "development"
LOG_LEVEL: str = "DEBUG"
print(f"ENVIROMENT : [{ENVIRONMENT}]")

HOST = config("HOST", default="*", cast=Csv())
ALLOWED_HOSTS = HOST
print(f"ALLOWED_HOSTS : {HOST}")


MIDDLEWARE.insert(1, "corsheaders.middleware.CorsMiddleware")


CORS_ALLOW_ALL_ORIGINS = True

DATABASES = {"default": dj_database_url.parse(config("DATABASE_LOCAL"))}


STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

# Exipiraicon del token
OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": 36000,  # 7200s 2 horas, por ejemplo
    "REFRESH_TOKEN_EXPIRATION": 43200,  # 30 Días
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": str(ERROR_LOG_FILE),
            "formatter": "default",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": True,
        },
        "custom": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
