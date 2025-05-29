from decouple import config

from django.conf import settings

from cryptography.fernet import Fernet, InvalidToken

from .logging_config import logger
from django.utils.timezone import now


CRYPTO_KEY = config("CRYPTO_KEY").encode()
fernet = Fernet(CRYPTO_KEY)


def build_db_config(camp) -> dict:
    """
    Recibe una instancia de Camp y retorna el diccionario de configuración
    de base de datos compatible con Django.
    """
    use_ssl = camp.db_host != "localhost"

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": camp.db_name,
        "USER": camp.db_user,
        "PASSWORD": camp.db_password,
        "HOST": camp.db_host,
        "PORT": str(camp.db_port),
        "TIME_ZONE": settings.TIME_ZONE,
        "CONN_HEALTH_CHECKS": True,
        "CONN_MAX_AGE": 300,  # keep connections open for 5 minutes
        "AUTOCOMMIT": True,
        "ATOMIC_REQUESTS": True,  # Each request will be a transaction
        "OPTIONS": {
            "sslmode": "require" if use_ssl else "disable",
        },
    }


def encrypt_value(value: str) -> bytes:
    return fernet.encrypt(value.encode())


def decrypt_value(value) -> str:
    if not value:
        return ""
    try:
        return fernet.decrypt(bytes(value)).decode()
    except (InvalidToken, TypeError, ValueError) as e:
        error_message = "No se pudo descifrar el valor proporcionado."

        logger.warning(
            f"{e.__class__.__module__}.{e.__class__.__name__}: {error_message}"
        )

        return ""


def get_client_ip(request):
    """Extrae la IP del cliente, útil para loguear."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def format_error_response(message: str, error_type: str, status_code: int):
    return {
        "detail": message,
        "error_type": error_type,
        "status_code": status_code,
        "timestamp": now().isoformat(),
    }
