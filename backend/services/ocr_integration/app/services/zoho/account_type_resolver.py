from typing import List
from pydantic import TypeAdapter


from app.services.ocr.schemas import Invoice
from app.services.openai.schemas.account_category import AccountCategory

from app.core.interface.account_provider import AccountingProvider
from app.services.zoho.schemas.chart_of_accounts_response import ZohoAccountResponse


async def build_classification_payload(
    invoice: Invoice, provider: AccountingProvider
) -> tuple[str, List[ZohoAccountResponse]]:
    # Adaptar cuentas
    raw_chart_of_accounts = await provider.get_chart_of_accounts()
    accounts: List[ZohoAccountResponse] = TypeAdapter(
        List[ZohoAccountResponse]
    ).validate_python(raw_chart_of_accounts)

    # construir texto descriptivo de la factura
    partner_name = invoice.partner_name
    items = [
        f"{line.quantity} x {line.product_name} a {line.price_unit} €"
        for line in invoice.invoice_lines
    ]

    text = f"El comercio: {partner_name} con los ítems: {', '.join(items)}"

    return text, accounts
