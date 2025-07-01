from contextlib import asynccontextmanager
from fastapi import FastAPI
from exponential_core.exceptions import (
    setup_exception_handlers,
    GlobalExceptionMiddleware,
)
from app.api.routes import entry
from app.core.lifespan import lifespan


app = FastAPI(
    title="base API",
    version="1.0",
    root_path="/orchestrator",
    lifespan=lifespan,
)

# Middleware global para manejar errores inesperados
app.add_middleware(GlobalExceptionMiddleware)
# Registrar rutas
app.include_router(entry.router)
# Registrar todos los exception handlers de forma automática
setup_exception_handlers(app)
