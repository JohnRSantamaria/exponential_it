from typing import List
from pydantic import TypeAdapter

from app.core.logging import logger
from app.core.interface.account_provider import AccountingProvider

from app.core.utils.comparator import are_similar
from app.services.ocr.schemas import Invoice
from app.services.openai.client import OpenAIService
from app.services.zoho.tax_resolver import get_tax_id
from app.services.zoho.schemas.bill_reponse import ZohoBillResponse
from app.services.zoho.account_type_resolver import build_classification_payload


async def get_bill_id(
    invoice: Invoice,
    provider: AccountingProvider,
):
    """Busca un bill_id usando el vendor id y el bill numeber si no existe lo crea."""

    # Obtener y parsear invoices
    raw_bills = await provider.get_all_bills()
    bills: List[ZohoBillResponse] = TypeAdapter(List[ZohoBillResponse]).validate_python(
        raw_bills
    )

    invoice_number = invoice.invoice_origin
    logger.info(f"Buscando factura con invoice number similar a: {invoice_number}")

    for bill in bills:
        if (
            are_similar(a=bill.bill_number, b=invoice_number, threshold=1.0)
            and bill.vendor_id == invoice.partner_id
        ):
            return bill.bill_id

    logger.warning("No se encontró una factura similar, creando nueva factura...")


async def create_bill_id(
    invoice: Invoice,
    provider: AccountingProvider,
    service: OpenAIService,
):
    # Incluir taxes
    logger.info("Creación u obtención de impuestos")
    await get_tax_id(invoice=invoice, provider=provider)

    ## Obtener valores de clasificación para el tipo de cuenta.
    text, accounts = await build_classification_payload(
        invoice=invoice, provider=provider
    )
    logger.info("Clasificando la cuenta a travéz de OpenAI")
    account_category = await service.classify_expense(text=text, accounts=accounts)
    invoice.account_category = account_category

    logger.info("Creando la factura")
    bill_data = await provider.create_bill(bill=invoice)
    bill_id = bill_data.get("bill_id")

    if not bill_id:
        raise ValueError("La respuesta del proveedor no conteine 'bill_id'")
    return bill_id
