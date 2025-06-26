from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.init_settings import inject_secrets
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar secretos (por ejemplo desde AWS Secrets Manager)
    await inject_secrets()

    # se puede agregar logs aquí si quieres saber que se cargaron
    logger.info("[LIFESPAN] Secretos cargados")

    yield

    # (Opcional) se puede hacer cleanup si luego agregas algo como cerrar sesión httpx, limpiar cachés, etc.
    logger.info("[LIFESPAN] Finalizando aplicación")
