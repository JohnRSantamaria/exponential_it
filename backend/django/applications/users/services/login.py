from users.models import User
from rest_framework import status
from users.utils.token_issuer import create_tokens_for_user
from core.log_utils import format_error_response


def login_user(email: str, password: str, account_id: int) -> tuple[bool, dict, int]:
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
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return (
            False,
            format_error_response(
                message="Credenciales inválidas",
                error_type="InvalidCredentials",
                status_code=status.HTTP_401_UNAUTHORIZED,
            ),
            status.HTTP_401_UNAUTHORIZED,
        )

    if not user.check_password(password):
        return (
            False,
            format_error_response(
                message="Credenciales inválidas",
                error_type="InvalidCredentials",
                status_code=status.HTTP_401_UNAUTHORIZED,
            ),
            status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return (
            False,
            format_error_response(
                message="Usuario inactivo",
                error_type="UserInactive",
                status_code=status.HTTP_403_FORBIDDEN,
            ),
            status.HTTP_403_FORBIDDEN,
        )

    tokens = create_tokens_for_user(user=user, account_id=account_id)
    return True, tokens, status.HTTP_200_OK
