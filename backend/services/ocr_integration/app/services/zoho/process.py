from app.core.enums import ServicesEnum
from app.core.adapter.base import get_provider
from app.core.logger import configure_logging
from app.services.ocr.schemas import Invoice, Supplier
from app.services.zoho.contact_resolver import get_or_create_contact_id

logger = configure_logging()


async def zoho_process(
    invoice: Invoice,
    supplier: Supplier,
):
    """Orquesta el proceso en Zoho."""
    logger.info("Inicia proceso en Zoho")
    provider = get_provider(service=ServicesEnum.ZOHO)

    contact_id = await get_or_create_contact_id(
        provider=provider, invoice=invoice, supplier=supplier
    )

    return {"contact_id": contact_id}
