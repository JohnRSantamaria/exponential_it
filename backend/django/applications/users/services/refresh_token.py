from rest_framework import status
from django.utils import timezone
from oauth2_provider.models import RefreshToken

from core.log_utils import format_error_response
from users.utils.token_issuer import create_tokens_for_user, REFRESH_TOKEN_EXPIRATION


def refresh_user_token(
    refresh_token_str: str, account_id: int
) -> tuple[bool, dict, int]:
    if not refresh_token_str:
        return (
            False,
            format_error_response(
                message="No se proporcionó refresh_token",
                error_type="MissingToken",
                status_code=status.HTTP_400_BAD_REQUEST,
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    if not account_id:
        return (
            False,
            format_error_response(
                message="No se proporcionó el account id",
                error_type="UnporcessableEntity",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        refresh = RefreshToken.objects.select_related(
            "access_token", "user", "application"
        ).get(token=refresh_token_str)
    except RefreshToken.DoesNotExist:
        return (
            False,
            format_error_response(
                message="Refresh token inválido",
                error_type="RefreshTokenError",
                status_code=status.HTTP_401_UNAUTHORIZED,
            ),
            status.HTTP_401_UNAUTHORIZED,
        )

    if not refresh.user.is_active:
        return (
            False,
            format_error_response(
                message="Usuario inactivo",
                error_type="UserInactive",
                status_code=status.HTTP_403_FORBIDDEN,
            ),
            status.HTTP_403_FORBIDDEN,
        )

    created_at = refresh.created or refresh.access_token.created
    if timezone.now() > created_at + REFRESH_TOKEN_EXPIRATION:
        refresh.access_token.delete()
        refresh.delete()
        return (
            False,
            format_error_response(
                message="Refresh token expirado",
                error_type="TokenExpired",
                status_code=status.HTTP_401_UNAUTHORIZED,
            ),
            status.HTTP_401_UNAUTHORIZED,
        )

    # Revocar tokens antiguos
    refresh.access_token.delete()
    refresh.delete()

    new_tokens = create_tokens_for_user(
        user=refresh.user,
        app=refresh.application,
        account_id=account_id,
    )

    return True, new_tokens, status.HTTP_200_OK
