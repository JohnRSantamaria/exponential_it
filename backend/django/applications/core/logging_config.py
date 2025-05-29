# applications\core\logging_config.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from django.conf import settings
from colorlog import ColoredFormatter

log_dir = Path(__file__).resolve().parents[1] / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / "errors.log"

# Define el nivel de log
log_level_str = (
    settings.LOG_LEVEL.upper()
    if settings.LOG_LEVEL
    else ("DEBUG" if settings.DEBUG else "WARNING")
)
log_level = getattr(logging, log_level_str, logging.WARNING)

# Handler para archivo .log
file_handler = RotatingFileHandler(
    filename=log_file,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,
    encoding="utf-8",
)

file_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d | %(message)s"
)
file_handler.setFormatter(file_formatter)

# Handler para consola con colores
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
    style="%",  # importante para usar % en el formato
)
console_handler.setFormatter(color_formatter)

# Silenciar algunos logs de librerías externas
logging.getLogger("oauthlib").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Configuración global
logging.basicConfig(level=log_level, handlers=[file_handler, console_handler])

logger = logging.getLogger("app")
