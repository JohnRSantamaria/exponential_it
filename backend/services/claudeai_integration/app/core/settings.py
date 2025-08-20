import os
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER", "").strip() == "1"
ENV_FILE = BASE_DIR / ".env.local" if not RUNNING_IN_DOCKER else None

if not RUNNING_IN_DOCKER and ENV_FILE and ENV_FILE.exists():
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=ENV_FILE)


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    DEBUG: bool = True

    # Logger
    LOG_LEVEL: str = "INFO"
    ERROR_LOG_FILE: Path = Field(default=BASE_DIR / "app" / "logs" / "errors.log")

    # DataBase
    DATABASE_URL: str

    # Jason Web Token
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str = ""
    CRYPTO_KEY: str = ""

    # Claude AI
    ANTHROPIC_API_KEY: str = ""

    @field_validator("ERROR_LOG_FILE", mode="before")
    @classmethod
    def convert_str_to_path(cls, v):
        return Path(v) if isinstance(v, str) else v

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
