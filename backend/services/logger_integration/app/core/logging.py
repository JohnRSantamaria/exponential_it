from exponential_core.logger.configure import configure_logging

from app.core.settings import settings

logger = configure_logging(
    log_level=settings.LOG_LEVEL,
    log_file=settings.ERROR_LOG_FILE,
    force=True,
)
