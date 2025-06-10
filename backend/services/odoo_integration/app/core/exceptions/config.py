# Configuración general (middleware, CORS, startup, etc.)
# app/core/middleware/error_handler.py
import httpx
from pydantic import ValidationError

from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.exceptions.format import format_error_response
from app.core.exceptions.types import CustomAppException
from app.core.logger import configure_logging

logger = configure_logging()


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"Unhandled exception: {str(exc)}")
            # try to extract the status code from the exception if possible
            status_code = 500
            if hasattr(exc, "status_code"):
                status_code = exc.status_code
            elif isinstance(exc, HTTPException):
                status_code = exc.status_code
            elif isinstance(exc, RequestValidationError):
                status_code = 422
            elif isinstance(exc, ValidationError):
                status_code = 422
            elif isinstance(exc, httpx.RequestError):
                status_code = 502
            elif isinstance(exc, httpx.HTTPStatusError) and exc.response:
                status_code = exc.response.status_code
            elif isinstance(exc, CustomAppException):
                status_code = exc.status_code

            logger.error(
                f"Excepción atrapada por middleware global | {request.method} {request.url} | "
                f"Tipo: {type(exc).__name__} | Código: {status_code} | Detalle: {str(exc)}",
                exc_info=exc,
            )

            return JSONResponse(
                status_code=status_code,
                content=format_error_response(
                    f"Internal server error : {str(exc)}", "UnhandledException", 500
                ),
            )
