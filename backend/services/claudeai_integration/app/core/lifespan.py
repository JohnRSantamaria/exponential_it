from fastapi import FastAPI
from contextlib import asynccontextmanager

from .logging import logger
from .settings import RUNNING_IN_DOCKER
from .init_settings import inject_secrets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan de contexto para FastAPI para manejar eventos de inicio y apagado."""
    await inject_secrets()

    if RUNNING_IN_DOCKER:
        logger.info("[LIFESPAN] Entorno: Docker")
    else:
        logger.info(f"[LIFESPAN] Entorno: Local")

    logger.info("[LIFESPAN] Secretos cargados")

    yield

    # (Opcional) se puede hacer cleanup si luego agregas algo como cerrar sesión httpx, limpiar cachés, etc.
    logger.info("[LIFESPAN] Finalizando aplicación")
