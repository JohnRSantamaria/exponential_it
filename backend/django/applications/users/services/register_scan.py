# applications/users/services/register_scan.py

from rest_framework import status
from users.services.scans import register_successful_scan
from core.log_utils import format_error_response


def handle_invoice_scan(user_id: int, account_id: int) -> tuple[bool, dict | None, int]:

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
