import os
from pathlib import Path
from typing import Literal
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

    # @JohnRSantamaria Open AI
    OPENAI_API_KEY: str = ""
    # Modelo para Chat Completions multimodal (imágenes + JSON)
    MODEL_NAME: str = "gpt-4o-mini"
    CHAT_MODEL: str = "gpt-4o-mini"

    # Render de PDF -> PNG
    MAX_PAGES: int = Field(
        default=2, description="Máximo de páginas a rasterizar por factura"
    )
    RENDER_DPI: int = Field(
        default=220, description="DPI usados para rasterizar PDF a PNG"
    )

    # Política de evidencias:
    # - off: no verificar evidencias contra el texto
    # - numbers: solo verificar que aparezca algún número del campo (ignora etiquetas); no rompe
    # - strict: verificar evidencias completas; si faltan, rompe con 422
    EVIDENCE_POLICY: Literal["off", "numbers", "strict"] = "numbers"

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
