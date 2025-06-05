from typing import Annotated

from fastapi import File, UploadFile
from app.core.settings import settings
from app.core.enums import ServicesEnum
from app.core.adapter.base import get_provider
from app.core.interface.provider_config import ProviderConfig
from app.core.logger import configure_logging
from app.services.ocr.schemas import Invoice, Supplier
from app.services.openai.client import OpenAIService
from app.services.zoho.bill_resolver import get_or_create_bill_id
from app.services.zoho.contact_resolver import get_or_create_contact_id

logger = configure_logging()


async def zoho_process(
    invoice: Invoice,
    supplier: Supplier,
    file: Annotated[UploadFile, File(...)],
    file_content: bytes,
):
    """Orquesta el proceso en Zoho."""
    logger.info("Inicia proceso en Zoho")
    provider = get_provider(service=ServicesEnum.ZOHO)
    service = OpenAIService(
        config=ProviderConfig(
            server_url=settings.URL_OPENAPI,
            api_prefix="/api/v1/openai",
        )
    )
    # Obtener el parnet VAT
    invoice_cif = invoice.partner_vat

    # Get or create vendor
    contact_id = await get_or_create_contact_id(
        provider=provider, invoice_cif=invoice_cif, supplier=supplier
    )
    invoice.partner_id = contact_id

    # Get or create invoice
    bill_id = await get_or_create_bill_id(
        provider=provider, invoice=invoice, service=service
    )

    # Upload File to Zoho
    await provider.attach_file_to_bill(
        bill_id=bill_id,
        file=file,
        file_content=file_content,
    )
