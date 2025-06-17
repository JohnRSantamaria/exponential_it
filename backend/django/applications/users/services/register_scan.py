# applications/users/services/register_scan.py

from rest_framework import status
from users.services.scans import register_successful_scan
from core.log_utils import format_error_response
from users.models import User


def handle_invoice_scan(
    user: User, user_id: int, jwt_data: dict
) -> tuple[bool, dict | None, int]:
    if user.id != user_id and not user.is_superuser:
        return (
            False,
            format_error_response(
                message="No autorizado",
                error_type="PermissionDenied",
                status_code=status.HTTP_403_FORBIDDEN,
            ),
            status.HTTP_403_FORBIDDEN,
        )

    account_id = jwt_data.get("account_info", {}).get("id")
    if not account_id:
        return (
            False,
            format_error_response(
                message="Token sin cuenta activa",
                error_type="MissingAccount",
                status_code=status.HTTP_400_BAD_REQUEST,
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    success, updated = register_successful_scan(user_id=user_id, account_id=account_id)
    if not success:
        return (
            False,
            format_error_response(
                message="Límite de facturas escaneadas alcanzado",
                error_type="LimitExceeded",
                status_code=status.HTTP_403_FORBIDDEN,
            ),
            status.HTTP_403_FORBIDDEN,
        )

    return (
        True,
        {
            "detail": "Contadores actualizados correctamente.",
            "user_total_invoices_scanned": updated["user"],
            "account_total_invoices_scanned": updated["account"],
        },
        status.HTTP_200_OK,
    )
