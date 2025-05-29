import traceback

from django.http import JsonResponse
from .log_utils import format_error_response


class GlobalExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            # Puedes registrar el error en logs si quieres
            print(traceback.format_exc())

            return JsonResponse(
                format_error_response(
                    message="Se produjo un error inesperado en el servidor",
                    error_type=exc.__class__.__name__,
                    status_code=500,
                ),
                status=500,
            )
