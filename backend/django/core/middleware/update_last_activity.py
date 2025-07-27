# core/middleware/update_last_activity.py
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser


class UpdateLastActivityMiddleware:
    """
    Middleware que actualiza el campo last_activity de un usuario autenticado.
    - Solo actualiza si el usuario está autenticado.
    - Ignora cualquier error sin interrumpir la request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            user = getattr(request, "user", None)

            if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
                user.last_activity = timezone.now()
                user.save(update_fields=["last_activity"])
        except Exception:
            # Se ignora cualquier excepción para no afectar la ejecución
            pass

        return self.get_response(request)
