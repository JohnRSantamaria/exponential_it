# app/core/exception_handlers.py
import httpx

from pydantic import ValidationError

from app.core.formats import format_error_response
from app.core.types import CustomAppException
from app.core.logger import logger

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            str(exc.detail), "HTTPException", exc.status_code
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=format_error_response(str(exc), "ValidationError", 422),
    )


async def pydantic_validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=format_error_response(str(exc), "PydanticValidation", 422),
    )


async def httpx_error_handler(request: Request, exc: httpx.RequestError):
    return JSONResponse(
        status_code=502,
        content=format_error_response(
            "Error al comunicarse con servicio externo", "ExternalServiceError", 502
        ),
    )


async def custom_app_exception_handler(request: Request, exc: CustomAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            exc.message, exc.__class__.__name__, exc.status_code
        ),
    )


async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Excepción no controlada", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=format_error_response(
            "Internal server error", "UnhandledException", 500
        ),
    )
