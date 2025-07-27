# core/exceptions.py
import datetime
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Captura cualquier excepción manejada por DRF y la devuelve con formato estándar.
    """
    # Llama al manejador por defecto de DRF
    response = exception_handler(exc, context)

    if response is None:
        # Si no es manejada por DRF (por ejemplo error 500 dentro de una vista)
        response_status = getattr(
            exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        detail = str(exc)
    else:
        response_status = response.status_code
        detail = response.data.get("detail", str(exc))

    # Devuelve siempre el formato estándar
    return Response(
        {
            "detail": detail,
            "error_type": exc.__class__.__name__,
            "status_code": response_status,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        },
        status=response_status,
    )
