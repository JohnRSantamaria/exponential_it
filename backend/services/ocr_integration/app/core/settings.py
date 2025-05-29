# app/core/settings.py
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import dotenv_values


BASE_DIR = Path(__file__).resolve().parents[2]

env_local = BASE_DIR / ".env.local"
debug_raw = dotenv_values(env_local).get("DEBUG", "true").strip().lower()

debug_mode = debug_raw in ["1", "true", "yes", "on"]

# Selección del archivo .env adecuado
env_file_to_use = env_local if debug_mode else BASE_DIR / ".env.prod"


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8004
    DEBUG: bool = True

    LOG_LEVEL: str = "INFO"

    # Jwt desde Django. Desencriptardor
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = env_file_to_use
        env_file_encoding = "utf-8"


settings = Settings()
