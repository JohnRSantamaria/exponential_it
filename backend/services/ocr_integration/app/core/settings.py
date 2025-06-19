# app/core/settings.py

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from dotenv import dotenv_values

# Base del proyecto: /backend/services/ocr_integration
BASE_DIR = Path(__file__).resolve().parents[2]

# Detectar si usar .env.local o .env.prod
env_local = BASE_DIR / ".env.local"
debug_raw = dotenv_values(env_local).get("DEBUG", "true").strip().lower()
debug_mode = debug_raw in ["1", "true", "yes", "on"]

env_file_to_use = env_local if debug_mode else BASE_DIR / ".env.prod"


class Settings(BaseSettings):
    # Configuración general del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = True

    # Id del servicio
    SERVICE_ID: int = 1

    # Logging
    LOG_LEVEL: str = "INFO"
    ERROR_LOG_FILE: Path = Field(default=BASE_DIR / "app" / "logs" / "errors.log")

    # JWT desde Django
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # DataBase
    DATABASE_URL: str

    # Crypto keys
    CRYPTO_KEY: str

    # services url
    URL_ZOHO: str
    URL_OPENAPI: str
    URL_ADMIN: str

    # Dropbox Credentials
    DROPBOX_ACCESS_TOKEN: str | None = None
    DROPBOX_REFRESH_TOKEN: str | None = None
    DROPBOX_APP_KEY: str | None = None
    DROPBOX_APP_SECRET: str | None = None

    # Taggun URL
    TAGGUN_URL: str = "https://api.taggun.io/api/receipt/v1/verbose/file"
    # TAGGUN_URL: str = "https://api.taggun.io/api/receipt/v1/verbose/encoded"

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
        env_file = env_file_to_use
        env_file_encoding = "utf-8"


settings = Settings()
