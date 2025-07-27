from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model

User = get_user_model()


class CookieJWTAuthentication(BaseAuthentication):
    """
    Autenticación basada únicamente en la cookie 'refresh_token'.
    No soporta Authorization: Bearer.
    """

    def authenticate(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return None

        try:
            token = RefreshToken(refresh_token)
            user = User.objects.get(id=token["user_id"])
            return (user, None)
        except (TokenError, User.DoesNotExist):
            return None
