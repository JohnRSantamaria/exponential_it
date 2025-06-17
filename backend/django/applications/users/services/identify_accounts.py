from users.models import User
from accounts.models import Account
from rest_framework import status
from core.log_utils import format_error_response


def identify_user_accounts(email: str, password: str) -> tuple[bool, dict, int]:
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

    accounts = Account.objects.filter(user=user).values("id", "name")
    return True, {"accounts": list(accounts)}, status.HTTP_200_OK
