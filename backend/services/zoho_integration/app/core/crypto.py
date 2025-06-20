from cryptography.fernet import Fernet, InvalidToken
from app.core.settings import settings
from app.core.logging import logger

fernet = Fernet(settings.CRYPTO_KEY)


def decrypt_value(value: bytes) -> str:
    if not value:
        return ""
    try:
        return fernet.decrypt(value).decode("utf-8")
    except (InvalidToken, TypeError, ValueError) as e:
        logger.warning(
            f"[DESCIFRADO] {e.__class__.__name__}: No se pudo descifrar el valor."
        )
        return ""
