import logging
from logging.handlers import RotatingFileHandler

from django.conf import settings
from colorlog import ColoredFormatter


def configure_logging():
    log_file = settings.ERROR_LOG_FILE

    print(f"CARPETA CONTENEDORA DEL LOG : {log_file}")

    log_level_str = (
        settings.LOG_LEVEL.upper()
        if getattr(settings, "LOG_LEVEL", None)
        else ("DEBUG" if settings.DEBUG else "WARNING")
    )
    log_level = getattr(logging, log_level_str, logging.WARNING)

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d | %(message)s"
    )
    file_handler.setFormatter(file_formatter)

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

    logging.getLogger("oauthlib").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.basicConfig(level=log_level, handlers=[file_handler, console_handler])
    return logging.getLogger("app")
