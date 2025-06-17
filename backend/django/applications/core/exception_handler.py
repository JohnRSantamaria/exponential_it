# applications\core\exception_handler.py
import logging
import traceback

from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

from applications.core.log_utils import format_error_response, get_client_ip


logger = logging.getLogger("app")


def custom_handler404(request, exception):
    logger.warning(
        f"404 Not Found: {request.path} | Método: {request.method} | IP: {get_client_ip(request)}"
    )
    return JsonResponse(
        format_error_response(
            message="La ruta solicitada no existe",
            error_type="NotFound",
            status_code=404,
        ),
        status=404,
    )


def custom_handler500(request):
    logger.error(
        f"500 Server Error: {request.path} | Método: {request.method} | IP: {get_client_ip(request)}",
        exc_info=True,
    )
    return JsonResponse(
        format_error_response(
            message="Se produjo un error inesperado",
            error_type="ServerError",
            status_code=500,
        ),
        status=500,
    )


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is not None:
        message = response.data.get("detail", str(response.data))
        exception_name = exc.__class__.__name__

        logger.warning(
            f"Excepción controlada: {exc.__class__.__module__}.{exception_name}: {message}"
        )
        return Response(
            format_error_response(
                message=message,
                error_type=exception_name,
                status_code=response.status_code,
            ),
            status=response.status_code,
        )

    logger.error(
        f"Excepción no controlada: {exc.__class__.__name__} | {str(exc)} | Contexto: {context.get('view')}",
        exc_info=True,
    )
    if settings.DEBUG:
        formatted_traceback = traceback.format_exc().splitlines()[-1]
        return Response(
            format_error_response(
                message=str(exc),
                error_type=exc.__class__.__name__,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            | {"traceback": formatted_traceback},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        format_error_response(
            message="Se produjo un error inesperado",
            error_type=exc.__class__.__name__,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
