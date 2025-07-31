from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.taggun.client import TaggunService
from app.core.client_provider import ProviderConfig
from app.core.settings import settings, RUNNING_IN_DOCKER
from app.core.init_settings import inject_secrets
from app.core.logging import logger

# Variable interna
_taggun_service: TaggunService | None = None


def get_taggun_service() -> TaggunService:
    """Devuelve siempre la instancia actual de TaggunService."""
    if _taggun_service is None:
        raise RuntimeError("TaggunService no está inicializado todavía")
    return _taggun_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _taggun_service

    await inject_secrets()

    logger.info(
        "[LIFESPAN] Entorno: Docker"
        if RUNNING_IN_DOCKER
        else "[LIFESPAN] Entorno: Local"
    )
    logger.info("[LIFESPAN] Secretos cargados correctamente")

    # Inicializar cliente
    _taggun_service = TaggunService(
        config=ProviderConfig(
            server_url=settings.TAGGUN_URL,
            api_key=settings.TAGGUN_APIKEY,
        ),
        max_concurrent_requests=5,
    )
    logger.info("[LIFESPAN] Cliente Taggun inicializado")

    try:
        yield
    finally:
        if _taggun_service:
            await _taggun_service.close()
            logger.info("[LIFESPAN] Cliente Taggun cerrado correctamente")

    logger.info("[LIFESPAN] Finalizando aplicación")
