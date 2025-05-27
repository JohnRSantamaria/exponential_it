# Punto de entrada principal de la app FastAPI
import httpx

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from app.api.routes import odoo
from app.core.config import GlobalExceptionMiddleware
from app.core.types import CustomAppException
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    pydantic_validation_handler,
    httpx_error_handler,
    custom_app_exception_handler,
    general_exception_handler,
)

app = FastAPI()

# Middleware global para manejar excepciones
app.add_middleware(GlobalExceptionMiddleware)

# Rutas
app.include_router(odoo.router, prefix="/api/v1")

# Handles global exceptions
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_handler)
app.add_exception_handler(httpx.RequestError, httpx_error_handler)
app.add_exception_handler(CustomAppException, custom_app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
