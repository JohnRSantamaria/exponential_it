from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class JWTRefreshCookieAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            request.user = AnonymousUser()
            return

        try:
            # Validar el refresh token
            token = RefreshToken(refresh_token)
            user_id = token["user_id"]
            user = User.objects.get(id=user_id)
            request.user = user
        except (TokenError, User.DoesNotExist):
            request.user = AnonymousUser()
