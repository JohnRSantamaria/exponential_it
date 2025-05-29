"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

from django.conf import settings
from django.core.wsgi import get_wsgi_application

from applications.core.logging_config import configure_logging
from config.set_up import set_up_environment

set_up_environment()

logger = configure_logging()
logger.info(f"\n🟢 WSGI iniciado correctamente entorno: {settings.ENVIRONMENT.upper()}")


application = get_wsgi_application()
