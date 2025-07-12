from fastapi import FastAPI
from exponential_core.exceptions import (
    setup_exception_handlers,
    GlobalExceptionMiddleware,
)
from app.api.routes import v16, v18
from app.core.lifespan import lifespan

# Crear instancia de FastAPI
app = FastAPI(
    title="ODOO API",
    version="1.0",
    root_path="/odoo",
    lifespan=lifespan,
)

# Middleware global para manejar errores inesperados
app.add_middleware(GlobalExceptionMiddleware)

# Registrar rutas
app.include_router(v16.router)
app.include_router(v18.router)

# Registrar todos los exception handlers de forma automática
setup_exception_handlers(app)
