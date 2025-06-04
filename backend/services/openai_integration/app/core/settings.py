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
    PORT: int = 8004
    DEBUG: bool = True

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

    # OpenAI Key
    OPENAI_API_KEY: str

    # Conversión de string a Path si se define por entorno
    @field_validator("ERROR_LOG_FILE", mode="before")
    @classmethod
    def convert_str_to_path(cls, v):
        return Path(v) if isinstance(v, str) else v

    class Config:
        env_file = env_file_to_use
        env_file_encoding = "utf-8"


settings = Settings()
