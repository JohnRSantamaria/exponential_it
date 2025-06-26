# Punto de entrada principal de la app FastAPI
from fastapi import FastAPI
from exponential_core.exceptions import (
    setup_exception_handlers,
    GlobalExceptionMiddleware,
)
from app.api.routes import entry
from app.core.lifespan import lifespan

app = FastAPI(
    title="OPENAI API",
    version="1.0",
    root_path="/openai",
    lifespan=lifespan,
)


# Middleware global para manejar excepciones
app.add_middleware(GlobalExceptionMiddleware)

# Rutas
app.include_router(entry.router, prefix="/api", tags=["api"])


# Middleware global para manejar errores inesperados
app.add_middleware(GlobalExceptionMiddleware)

# Registrar rutas
app.include_router(entry.router, prefix="/api", tags=["api"])

# Registrar todos los exception handlers de forma automática
setup_exception_handlers(app)
