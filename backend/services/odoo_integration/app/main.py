from fastapi import FastAPI
from exponential_core.logger import configure_logging
from exponential_core.exceptions import (
    setup_exception_handlers,
    GlobalExceptionMiddleware,
)
from app.api.routes import entry

# Crear instancia de FastAPI
app = FastAPI(title="ODOO API", version="1.0", root_path="/odoo")

# Configurar logger centralizado
logger = configure_logging()

# Middleware global para manejar errores inesperados
app.add_middleware(GlobalExceptionMiddleware)

# Registrar rutas
app.include_router(entry.router, prefix="/api", tags=["api"])

# Registrar todos los exception handlers de forma automática
setup_exception_handlers(app)
