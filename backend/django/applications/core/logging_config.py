# applications\core\logging_config.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from django.conf import settings


log_dir = Path(__file__).resolve().parents[1] / "logs"
log_dir.mkdir(parents=True, exist_ok=True)


log_file = log_dir / "errors.log"


log_level = (
    logging.DEBUG
    if settings.DEBUG
    else getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
)

file_handler = RotatingFileHandler(
    filename=log_file,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,  # conserva los últimos 3 logs antiguos
    encoding="utf-8",
)


formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d | %(message)s"
)

file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logging.getLogger("oauthlib").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logging.basicConfig(level=log_level, handlers=[file_handler, console_handler])


logger = logging.getLogger("app")


"""
from app.core.logger import logger

logger.info("Aplicación iniciada")
logger.error("Fallo inesperado", exc_info=True)
logger.warning("Este es un aviso")
logger.debug("Información de depuración detallada")

"""
