"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

from django.conf import settings
from django.core.wsgi import get_wsgi_application

from config.set_up import set_up_environment

from applications.core.logging_config import logger

set_up_environment()
try:
    logger.info(
        f"\n🟢 WSGI iniciado correctamente entorno: {settings.ENVIRONMENT.upper()}"
    )
except Exception as e:
    print(e)
application = get_wsgi_application()
