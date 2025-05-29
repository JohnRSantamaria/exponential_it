import traceback

from camps.models import Camp
from applications.core.db_utils import format_error_response
from applications.core.db_context import set_current_camp

from django.http import JsonResponse
from django.db.utils import ProgrammingError, OperationalError


class CampDetectionMiddleware:
    """
    Middleware para detectar el campamento actual a partir de la cabecera 'X-Camp-Token'.

    - Omite rutas centrales como /admin/, /static/, /docs/, etc.
    - Requiere cabecera X-Camp-Token para rutas normales.
    - Si el modelo Camp no está disponible (por ejemplo, durante migraciones), devuelve error controlado.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if (
            path.startswith("/admin/")
            or path.startswith("/static/")
            or path.startswith("/favicon")
            or path.startswith("/docs/")
        ):
            return self.get_response(request)

        token = request.headers.get("X-Camp-Token")

        if not token:
            return JsonResponse(
                {"detail": "Cabecera 'X-Camp-Token' requerida"},
                status=400,
            )

        try:
            camp = Camp.objects.filter(name=token, active=True).first()
        except (ProgrammingError, OperationalError) as e:
            return JsonResponse(
                {
                    "detail": "❌ Error de base de datos al acceder a los campamentos.",
                    "error": str(e),
                },
                status=500,
            )

        if not camp:
            return JsonResponse(
                {"detail": f"Campamento con token '{token}' no encontrado o inactivo"},
                status=403,
            )

        set_current_camp(camp)
        return self.get_response(request)


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
