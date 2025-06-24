from fastapi import FastAPI
from exponential_core.exceptions import (
    setup_exception_handlers,
    GlobalExceptionMiddleware,
)
from app.api.routes import entry

# Crear instancia de FastAPI
app = FastAPI(title="base API", version="1.0", root_path="/orchestator")

# Middleware global para manejar errores inesperados
app.add_middleware(GlobalExceptionMiddleware)

# Registrar rutas
app.include_router(entry.router, prefix="/entry", tags=["api"])

# Registrar todos los exception handlers de forma automática
setup_exception_handlers(app)
