# config\settings\local.py
import os
from .base import *

import dj_database_url

DEBUG = True

ENVIRONMENT: str = "development"
LOG_LEVEL: str = "DEBUG"

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]


MIDDLEWARE.insert(1, "corsheaders.middleware.CorsMiddleware")


CORS_ALLOW_ALL_ORIGINS = True

DATABASES = {"default": dj_database_url.parse(config("DATABASE_LOCAL"))}


STATIC_URL = "static/"

# Exipiraicon del token
OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": 36000,  # 7200s 2 horas, por ejemplo
    "REFRESH_TOKEN_EXPIRATION": 43200,  # 30 Días
}

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

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
            "filename": os.path.join(BASE_DIR, "logs", "errors.log"),
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
