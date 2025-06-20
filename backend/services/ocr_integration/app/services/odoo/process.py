from app.core.adapter.base import get_provider
from app.core.enums import ServicesEnum
from app.services.ocr.schemas import Invoice, Supplier
from app.core.logging import logger
from exponential_core.exceptions import CustomAppException


async def odoo_process(invoice: Invoice, supplier: Supplier):
    """Orquesta el proceso en Odoo"""
    logger.debug("Inicia el proceso en Odoo")
    provider = get_provider(service=ServicesEnum.ODOO)

    company_vat = invoice.company_vat
    if not company_vat:
        CustomAppException(message="Necesita crear el VAT para la empresa.")

    provider.create_company(name=invoice.company_vat)  # Enviar el CIF, VAT de Company
