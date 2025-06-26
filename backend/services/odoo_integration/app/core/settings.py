import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from exponential_core.secrets import SecretManager

# Base del proyecto: /backend/services/odoo_integration
BASE_DIR = Path(__file__).resolve().parents[2]

# Detectar si estamos en Docker (usado solo para saber si se carga el .env.local o no)
RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER", "").strip() == "1"
ENV_FILE = BASE_DIR / ".env.local" if not RUNNING_IN_DOCKER else None

# 📦 Cargar manualmente el .env.local si no estamos en Docker
if not RUNNING_IN_DOCKER and ENV_FILE and ENV_FILE.exists():
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=ENV_FILE)

# Instancia global del SecretManager con nombre base de secreto
secret_manager = SecretManager(
    base_secret_name="exponentialit/core",
    default_ttl_seconds=300,
)

# Carga y cachea los secretos específicos para esta app
aws_secrets = secret_manager.get_secret() or {}


class Settings(BaseSettings):
    # ⚙️ Configuración general del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8004
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str
    ERROR_LOG_FILE: Path = Field(default=BASE_DIR / "app" / "logs" / "errors.log")

    # JWT
    JWT_SECRET_KEY: str = aws_secrets.get("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"

    # Base de datos
    DATABASE_URL: str

    # Criptografía interna
    CRYPTO_KEY: str = aws_secrets.get("CRYPTO_KEY", "")

    # (opcional) declarar las variables si quieres usarlas
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_DEFAULT_REGION: str = "eu-west-3"

    @field_validator("ERROR_LOG_FILE", mode="before")
    @classmethod
    def convert_str_to_path(cls, v):
        return Path(v) if isinstance(v, str) else v

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
