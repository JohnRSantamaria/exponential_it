# app/core/init_settings.py
from exponential_core.secrets import SecretManager
from app.core.settings import settings


async def inject_secrets():
    manager = SecretManager(base_secret_name="exponentialit/core")
    secrets = await manager.get_secret() or {}

    settings.JWT_SECRET_KEY = secrets.get("JWT_SECRET_KEY", "")
    settings.CRYPTO_KEY = secrets.get("CRYPTO_KEY", "")
    settings.TAGGUN_APIKEY = secrets.get("TAGGUN_API_KEY", "")
