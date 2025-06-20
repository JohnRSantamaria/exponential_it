# Punto de entrada principal de la app FastAPI
from fastapi import FastAPI
from app.api.routes import auth, books
from exponential_core.exceptions import (
    setup_exception_handlers,
    GlobalExceptionMiddleware,
)

# Crear instancia de FastAPI
app = FastAPI(title="OCR API", version="1.0", root_path="/ocr")
# Rutas

# Middleware global para manejar errores inesperados
app.add_middleware(GlobalExceptionMiddleware)

# Registrar rutas
app.include_router(auth.router, prefix="/api")
app.include_router(books.router, prefix="/api")


# Registrar todos los exception handlers de forma automática
setup_exception_handlers(app)
