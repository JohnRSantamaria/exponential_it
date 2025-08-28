# app/core/lifespan.py
import asyncpg
from contextlib import asynccontextmanager
from .settings import settings, RUNNING_IN_DOCKER
from .logging import logger
from ..services.logger.db_init import ensure_schema


@asynccontextmanager
async def lifespan(app):
    logger.info("[LIFESPAN] Entorno: %s", "Docker" if RUNNING_IN_DOCKER else "Local")
    app.state.DB_DSN = settings.DATABASE_URL
    app.state.pool = await asyncpg.create_pool(
        settings.DATABASE_URL, min_size=1, max_size=10
    )
    await ensure_schema(app.state.pool)
    try:
        yield
    finally:
        await app.state.pool.close()
        logger.info("[LIFESPAN] Finalizando aplicación")
