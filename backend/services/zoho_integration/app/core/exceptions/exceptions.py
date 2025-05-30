# app/core/exception_handlers.py
import httpx

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.core.exceptions.format import format_error_response
from app.core.logger import configure_logging
from app.core.exceptions.types import CustomAppException

logger = configure_logging()


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Cuándo se usa:
        Se activa automáticamente cuando se lanza una excepción HTTPException
        (por ejemplo, al usar raise HTTPException(status_code=404, detail="No encontrado")).

    Uso típico:
        -Accesos denegados (403)
        -Recurso no encontrado (404)
        -Errores definidos por FastAPI en las rutas
    """

    logger.warning(f"HTTPException {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            str(exc.detail), "HTTPException", exc.status_code
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Cuándo se usa:
        Manejador de excepciones de FastAPI para errores en la validación de solicitudes
        (RequestValidationError), cuando los datos del request no cumplen con el esquema
        esperado en query, body, path o form.

    Uso típico:
        -Campos faltantes en un POST
        -Valores con formato incorrecto en query parameters
    """
    logger.warning(f"RequestValidationError en {request.url.path} | Detalle: {exc}")
    return JSONResponse(
        status_code=422,
        content=format_error_response(str(exc), "ValidationError", 422),
    )


async def pydantic_validation_handler(request: Request, exc: ValidationError):
    """
    Cuándo se usa:
        Se activa cuando una validación con Pydantic falla directamente, es decir,
        fuera del contexto del request de FastAPI (por ejemplo, en validaciones internas o servicios).

    Uso típico:
        - Validación manual con modelos Pydantic (MyModel(**data))
        - Conversión y validación de datos internos que no provienen del request
    """
    logger.warning(f"Pydantic ValidationError en {request.url.path} | Detalle: {exc}")
    return JSONResponse(
        status_code=422,
        content=format_error_response(str(exc), "PydanticValidation", 422),
    )


async def httpx_error_handler(request: Request, exc: httpx.RequestError):
    """
    Cuándo se usa:
        Captura errores de red o comunicación con servicios externos usando httpx.

    Uso típico:
        - Fallo en una llamada a una API externa (timeout, conexión rechazada, DNS)
        - Problemas de red temporales al hacer requests asíncronos con httpx

    Ejemplo:
        try:
            await httpx.get("https://external.api.com")
        except httpx.RequestError as exc:
            raise exc  # Esto activa este handler
    """
    logger.error(f"Error de red con servicio externo en {request.url} | {repr(exc)}")
    return JSONResponse(
        status_code=502,
        content=format_error_response(
            "Error al comunicarse con servicio externo", "ExternalServiceError", 502
        ),
    )


async def custom_app_exception_handler(request: Request, exc: CustomAppException):
    """
    Cuándo se usa:
        Se activa cuando se lanza una excepción personalizada definida por el desarrollador,
        derivada de CustomAppException.

    Uso típico:
        - Errores de lógica de negocio controlados (por ejemplo: usuario no tiene suscripción)
        - Respuestas personalizadas y detalladas sin usar HTTPException

    Ventaja:
        Permite enviar mensajes y status code definidos con control total desde cualquier parte del código.
    """
    logger.error(
        f"CustomAppException {exc.status_code} en {request.url.path} | {exc.message}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            exc.message, exc.__class__.__name__, exc.status_code
        ),
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Cuándo se usa:
        Captura cualquier excepción no controlada por los handlers anteriores.

    Uso típico:
        - Errores inesperados en lógica interna
        - Fallback general para proteger el sistema de caídas y registrar el error

    Recomendación:
        Siempre mantener este handler para evitar exponer detalles internos al cliente.
        Registra la excepción con traceback completo en los logs para depuración.
    """
    logger.critical(
        f"Excepción no controlada en {request.url.path} | {type(exc).__name__}",
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content=format_error_response(
            "Internal server error", "UnhandledException", 500
        ),
    )
