# applications/core/decorators.py
from functools import wraps
from django.http import JsonResponse
from django.db.utils import ProgrammingError, OperationalError
from camps.models import Camp
from applications.core.db_context import set_current_camp


def require_camp_token(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
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
        return view_func(request, *args, **kwargs)

    return _wrapped_view


# # applications/schedule/views.py
# from django.http import JsonResponse
# from applications.core.decorators import require_camp_token


# @require_camp_token
# def list_activities(request):
#     return JsonResponse({"ok": True, "camp": "válido"})
