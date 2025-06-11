import os
import dj_database_url

from .base import *


DEBUG = False

ENVIRONMENT: str = "production"
LOG_LEVEL: str = "ERROR"


HOST = config("HOST", default="15.188.6.72", cast=str)
ALLOWED_HOSTS = [f"{HOST}"]

MIDDLEWARE.insert(1, "corsheaders.middleware.CorsMiddleware")

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [f"http://{HOST}"]

DATABASES = {"default": dj_database_url.parse(config("DATABASE_PROD"))}

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Exipiraicon del token
OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": 300,  # 7200s 2 horas, por ejemplo
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
