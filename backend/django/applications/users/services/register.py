from users.serializers import UserCreateSerializer
from rest_framework import status
from core.log_utils import format_error_response


def register_user(data: dict) -> tuple[bool, dict, int]:
    serializer = UserCreateSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return (
            True,
            {"message": "Usuario creado correctamente"},
            status.HTTP_201_CREATED,
        )

    return (
        False,
        (
            format_error_response(
                message="Datos inválidos",
                error_type="ValidationError",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            | {"errors": serializer.errors}
        ),
        status.HTTP_400_BAD_REQUEST,
    )
