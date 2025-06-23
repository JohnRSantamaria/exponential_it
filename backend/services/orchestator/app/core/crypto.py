from cryptography.fernet import Fernet, InvalidToken
from app.core.settings import settings

fernet = Fernet(settings.CRYPTO_KEY)


def decrypt_value(value: bytes) -> str:
    if not value:
        return ""
    try:
        return fernet.decrypt(value).decode("utf-8")
    except (InvalidToken, TypeError, ValueError) as e:
        return ""
