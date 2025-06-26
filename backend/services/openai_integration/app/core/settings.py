# app/core/settings.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


# Base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER", "").strip() == "1"
ENV_FILE = BASE_DIR / ".env.local" if not RUNNING_IN_DOCKER else None

if not RUNNING_IN_DOCKER and ENV_FILE and ENV_FILE.exists():
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=ENV_FILE)


class Settings(BaseSettings):
    # Configuración general del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    ERROR_LOG_FILE: Path = Field(default=BASE_DIR / "app" / "logs" / "errors.log")

    # DataBase
    DATABASE_URL: str

    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str = ""
    CRYPTO_KEY: str = ""
    OPENAI_API_KEY: str = ""

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
