# Configuración general (middleware, CORS, startup, etc.)
# app/core/middleware/error_handler.py
import httpx
from pydantic import ValidationError
from datetime import datetime, timezone

from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


from app.core.logger import logger
from app.core.types import CustomAppException


def format_error_response(
    message: str,
    error_type: str,
    status_code: int,
):
    return {
        "detail": message,
        "error_type": error_type,
        "status_code": status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


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

            return JSONResponse(
                status_code=status_code,
                content=format_error_response(
                    f"Internal server error : {str(exc)}", "UnhandledException", 500
                ),
            )
