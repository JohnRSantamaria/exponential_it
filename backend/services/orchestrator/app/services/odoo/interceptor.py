import functools
import traceback

from fastapi import HTTPException
import httpx

from app.core.logging import logger
from app.services.odoo.exceptions import (
    OdooConnectionError,
    OdooTimeoutError,
    OdooUnexpectedError,
)


def error_interceptor(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            response = await func(*args, **kwargs)

            if isinstance(response, list):
                return response

            if isinstance(response, dict):
                code = int(response.pop("code", 0))
                message = response.pop("message", None)
                error_type = response.pop("error_type", None)

                if code != 0:
                    error_message = f"[OdooError] Código: {code}, mensaje: {message}"
                    logger.error(error_message)
                    raise HTTPException(status_code=500, detail=error_message)

                if error_type:
                    detail = response.get(
                        "detail", "error en el servicio de Odoo integration"
                    )
                    status_code = int(response.get("status_code", 500))
                    logger.error(f"[OdooError] Tipo: {error_type}, Detalle: {detail}")
                    raise HTTPException(status_code=status_code, detail=detail)
                if len(response) == 1:
                    return list(response.values())[0]
            return response

        except httpx.TimeoutException as e:
            logger.error(f"[OdooTimeout] {e}")
            raise OdooTimeoutError()

        except httpx.ConnectError as e:
            logger.error(f"[OdooConnectionError] {e}")
            raise OdooConnectionError(
                message=f"[OdooConnectionError] No se pudo conectar con el microservicio de Odoo"
            )

        except httpx.RequestError as e:
            logger.error(f"[OdooRequestError] {e}")
            raise OdooUnexpectedError(
                message="Error de solicitud a Odoo", data={"detail": str(e)}
            )

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"[UnhandledOdooError] {str(e)}\nTraceback:\n{tb}")
            raise OdooUnexpectedError(message=str(e))

    return wrapper
