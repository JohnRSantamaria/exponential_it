# app/core/settings.py
import os
from pathlib import Path
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
    # Configuración general del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    ERROR_LOG_FILE: Path = Field(default=BASE_DIR / "app" / "logs" / "errors.log")

    # JWT desde Django
    JWT_SECRET_KEY: str = aws_secrets.get("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"

    # DataBase
    DATABASE_URL: str

    # Crypto keys
    CRYPTO_KEY: str = aws_secrets.get("CRYPTO_KEY", "")

    # URLs de los servicios de ExponentialIT
    URL_ADMIN: str

    # Taggun URL
    TAGGUN_URL: str = "https://api.taggun.io/api/receipt/v1/verbose/file"
    TAGGUN_APIKEY: str = aws_secrets.get("TAGGUN_API_KEY", "")

    # Timeout para HTTPX
    HTTP_TIMEOUT_CONNECT: float = Field(
        default=10.0,
        description="Tiempo máximo (en segundos) para establecer la conexión HTTP",
    )
    HTTP_TIMEOUT_READ: float = Field(
        default=60.0,
        description="Tiempo máximo (en segundos) para recibir la respuesta completa del servidor",
    )
    HTTP_TIMEOUT_WRITE: float = Field(
        default=10.0,
        description="Tiempo máximo (en segundos) para enviar el cuerpo de la solicitud HTTP",
    )
    HTTP_TIMEOUT_POOL: float = Field(
        default=5.0,
        description="Tiempo máximo (en segundos) para obtener una conexión disponible del pool de conexiones",
    )

    # Conversión de string a Path si se define por entorno
    @field_validator("ERROR_LOG_FILE", mode="before")
    @classmethod
    def convert_str_to_path(cls, v):
        return Path(v) if isinstance(v, str) else v

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
