# Punto de entrada principal de la app FastAPI
import httpx

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from app.api.routes import orc
from app.core.logger import configure_logging
from app.core.exceptions.types import CustomAppException
from app.core.exceptions.config import GlobalExceptionMiddleware
from app.core.exceptions.exceptions import (
    custom_app_exception_handler,
    general_exception_handler,
    http_exception_handler,
    httpx_error_handler,
    pydantic_validation_handler,
    validation_exception_handler,
)

app = FastAPI(title="OCR API", version="1.0", root_path="/ocr")

# Logger
logger = configure_logging()

# Middleware global para manejar excepciones
app.add_middleware(GlobalExceptionMiddleware)

# Rutas
app.include_router(orc.router, prefix="/api", tags=["api"])

# Handles global exceptions
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_handler)
app.add_exception_handler(httpx.RequestError, httpx_error_handler)
app.add_exception_handler(CustomAppException, custom_app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
