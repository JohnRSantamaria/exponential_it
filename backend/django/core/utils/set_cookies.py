from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def set_jwt_cookies(response, user):
    try:
        refresh = RefreshToken.for_user(user)
    except Exception as e:
        print(f"⚠️ Error generando refresh token: {e}")
        return response  # Devuelve la respuesta sin cookie si falla

    is_prod = not settings.DEBUG
    response.set_cookie(
        key="refresh_token",
        value=str(refresh),
        httponly=True,
        secure=is_prod,
        samesite="Lax" if settings.DEBUG else "None",
        path="/",
    )
    return response
