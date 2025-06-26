# app/core/init_settings.py
from exponential_core.secrets import SecretManager
from exponential_core.exceptions import AWSConnectionError
from app.core.settings import settings


async def inject_secrets():
    try:
        manager = SecretManager(base_secret_name="exponentialit/core")
        secrets = await manager.get_secret() or {}

        settings.JWT_SECRET_KEY = secrets.get("JWT_SECRET_KEY", "")
        settings.CRYPTO_KEY = secrets.get("CRYPTO_KEY", "")
    except Exception as e:
        raise AWSConnectionError(
            detail=f"Fallo al conectar con AWS Secrets Manager: {str(e)}"
        ) from e
