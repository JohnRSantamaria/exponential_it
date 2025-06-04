from typing import List

from pydantic import TypeAdapter
from app.core.interface.account_provider import AccountingProvider
from app.core.logger import configure_logging
from app.services.ocr.schemas import Invoice, Supplier
from app.services.zoho.account_type_resolver import find_matching_account_id
from app.services.zoho.schemas.bill_reponse import ZohoBill
from app.services.zoho.tax_resolver import get_tax_id
from app.utils.comparator import are_similar

logger = configure_logging()


async def get_or_create_bill_id(
    invoice: Invoice, supplier: Supplier, provider: AccountingProvider
):
    """Busca un bill_id usando el vendor id y el bill numeber si no existe lo crea."""

    # Obtener y parsear invoices
    raw_bills = await provider.get_all_bills()
    bills: List[ZohoBill] = TypeAdapter(List[ZohoBill]).validate_python(raw_bills)

    invoice_number = invoice.invoice_origin
    logger.info(f"Buscando factura con invoice number similar a: {invoice_number}")

    for bill in bills:
        if (
            are_similar(a=bill.bill_number, b=invoice_number, threshold=1.0)
            and bill.vendor_id == invoice.partner_id
        ):
            return bill.bill_id

    logger.warning("No se encontró una factura similar, creando nueva factura...")

    # Incluir taxes
    logger.info("Creación u obtención de impuestos")
    await get_tax_id(invoice=invoice, provider=provider)

    invoice
    # Incluir tipo de cuenta
    await find_matching_account_id(invoice=invoice, provider=provider)

    bill_data = await provider.create_bill(bill=invoice)
