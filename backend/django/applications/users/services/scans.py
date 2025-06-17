# applications/users/services/scans.py

from django.db import transaction
from users.models import User
from accounts.models import Account


def register_successful_scan(
    user_id: int, account_id: int, quantity: int = 1
) -> tuple[bool, dict]:
    """
    Incrementa los contadores de facturas escaneadas a nivel de usuario y cuenta.
    Retorna una tupla (success, updated_values).
    """
    with transaction.atomic():
        user = User.objects.select_for_update().get(id=user_id)
        if user.total_invoices_scanned + quantity > 1000:
            return False, {}

        account = Account.objects.select_for_update().get(id=account_id, user=user)

        # Incrementar contadores
        user.total_invoices_scanned += quantity
        account.total_invoices_scanned += quantity

        user.save(update_fields=["total_invoices_scanned"])
        account.save(update_fields=["total_invoices_scanned"])

        return True, {
            "user": user.total_invoices_scanned,
            "account": account.total_invoices_scanned,
        }
