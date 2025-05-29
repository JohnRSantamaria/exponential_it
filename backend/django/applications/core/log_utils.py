import logging

from decouple import config
from django.utils.timezone import now
from cryptography.fernet import Fernet, InvalidToken

CRYPTO_KEY = config("CRYPTO_KEY").encode()
fernet = Fernet(CRYPTO_KEY)
logger = logging.getLogger("app")


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
