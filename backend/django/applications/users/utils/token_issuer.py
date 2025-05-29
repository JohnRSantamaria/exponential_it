# applications\users\utils\token_issuer.py
from datetime import timedelta
from django.utils import timezone
from oauthlib.common import generate_token
from oauth2_provider.models import AccessToken, RefreshToken, Application

from django.conf import settings


from .serialize_jwt import sign_jwt


ACCESS_TOKEN_EXPIRATION = timedelta(
    seconds=settings.OAUTH2_PROVIDER.get("ACCESS_TOKEN_EXPIRE_SECONDS", 300)
)
REFRESH_TOKEN_EXPIRATION = timedelta(
    seconds=settings.OAUTH2_PROVIDER.get("REFRESH_TOKEN_EXPIRATION", 2592000)
)


def create_tokens_for_user(user, app=None):
    if app is None:
        app, _ = Application.objects.get_or_create(
            name="default",
            defaults={
                "client_type": Application.CLIENT_CONFIDENTIAL,
                "authorization_grant_type": Application.GRANT_PASSWORD,
                "user": user,
            },
        )

    # Crear Access Token
    access_token = AccessToken.objects.create(
        user=user,
        application=app,
        token=generate_token(),
        expires=timezone.now() + ACCESS_TOKEN_EXPIRATION,
        scope="read write",
    )

    # Crear Refresh Token
    refresh_token = RefreshToken.objects.create(
        user=user,
        token=generate_token(),
        access_token=access_token,
        application=app,
    )

    # Servicios activos
    services = user.user_services.filter(is_active=True).select_related("service")
    service_codes = [s.service.code for s in services]

    # JWT
    app_token = sign_jwt(
        {
            "sub": str(user.id),
            "email": user.email,
            "services": service_codes,
            "exp": int((timezone.now() + ACCESS_TOKEN_EXPIRATION).timestamp()),
        }
    )

    return {
        "access_token": access_token.token,
        "refresh_token": refresh_token.token,
        "token_type": "Bearer",
        "expires_in": int(ACCESS_TOKEN_EXPIRATION.total_seconds()),
        "refresh_token_expires_in": int(REFRESH_TOKEN_EXPIRATION.total_seconds()),
        "refresh_token_expires_at": int(
            (timezone.now() + REFRESH_TOKEN_EXPIRATION).timestamp()
        ),
        "scope": access_token.scope,
        "app_token": app_token,
    }
