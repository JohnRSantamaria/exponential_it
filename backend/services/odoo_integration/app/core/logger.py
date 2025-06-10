# app/core/logger.py

import logging
import warnings

from pathlib import Path
from colorlog import ColoredFormatter
from logging.handlers import RotatingFileHandler

from app.core.settings import settings


def configure_logging():
    log_file = settings.ERROR_LOG_FILE
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Determinar nivel de log
    log_level_str = (
        settings.LOG_LEVEL.upper()
        if getattr(settings, "LOG_LEVEL", None)
        else ("DEBUG" if settings.DEBUG else "WARNING")
    )
    log_level = getattr(logging, log_level_str, logging.WARNING)

    # File handler con rotación
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d | %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler con colores
    console_handler = logging.StreamHandler()
    color_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d | %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
        style="%",
    )
    console_handler.setFormatter(color_formatter)

    # Configuración base
    logging.basicConfig(level=log_level, handlers=[file_handler, console_handler])
    logger = logging.getLogger("app")

    # Ajustar loggers de librerías externas si es necesario
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    def custom_warning_handler(
        message, category, filename, lineno, file=None, line=None
    ):
        if issubclass(category, RuntimeWarning):
            logger.warning(f"RuntimeWarning: {message} ({filename}:{lineno})")

    warnings.showwarning = custom_warning_handler

    return logger
