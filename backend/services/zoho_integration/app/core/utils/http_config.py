# app/core/http_config.py

import httpx
from app.core.settings import settings


def get_default_httpx_timeout() -> httpx.Timeout:
    return httpx.Timeout(
        connect=settings.HTTP_TIMEOUT_CONNECT,
        read=settings.HTTP_TIMEOUT_READ,
        write=settings.HTTP_TIMEOUT_WRITE,
        pool=settings.HTTP_TIMEOUT_POOL,
    )
