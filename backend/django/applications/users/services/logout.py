from rest_framework import status
from oauth2_provider.models import AccessToken, RefreshToken
from core.log_utils import format_error_response


def logout_user(token_str: str) -> tuple[bool, dict, int]:
    if not token_str:
        return (
            False,
            format_error_response(
                message="Token no proporcionado o inválido",
                error_type="TokenMissing",
                status_code=status.HTTP_400_BAD_REQUEST,
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        access_token = AccessToken.objects.select_related("refresh_token").get(
            token=token_str
        )
    except AccessToken.DoesNotExist:
        return (
            False,
            format_error_response(
                message="Token no encontrado",
                error_type="AccessTokenNotFound",
                status_code=status.HTTP_404_NOT_FOUND,
            ),
            status.HTTP_404_NOT_FOUND,
        )

    # Eliminar refresh token vinculado
    RefreshToken.objects.filter(access_token=access_token).delete()
    access_token.delete()

    return True, {"detail": "Sesión cerrada correctamente."}, status.HTTP_200_OK
