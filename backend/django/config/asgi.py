"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

from django.conf import settings
from django.core.asgi import get_asgi_application

from config.set_up import set_up_environment

from applications.core.logging_config import logger

set_up_environment()

logger.info(f"\n🟢 ASGI iniciado correctamente entorno: {settings.ENVIRONMENT.upper()}")

application = get_asgi_application()
