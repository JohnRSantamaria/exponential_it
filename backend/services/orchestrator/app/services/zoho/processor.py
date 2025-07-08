from fastapi import UploadFile
from app.core.logging import logger
from app.core.schemas.enums import ServicesEnum
from app.core.patterns.adapter.base import get_provider
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.zoho.client import get_or_create_bill, get_or_create_contact_id


async def zoho_process(
    file: UploadFile,
    file_content: bytes,
    taggun_data: TaggunExtractedInvoice,
    company_vat: str,
):
    zoho_provider = get_provider(
        service=ServicesEnum.ZOHO,
        company_vat=company_vat,
    )

    partner_id = await get_or_create_contact_id(
        zoho_provider=zoho_provider,
        taggun_data=taggun_data,
    )
    logger.debug("Obtención del proveedor en Zoho completada")

    await get_or_create_bill(
        zoho_provider=zoho_provider,
        taggun_data=taggun_data,
        partner_id=partner_id,
        file=file,
        file_content=file_content,
    )
    logger.debug("Obtención de la factura en Zoho completada")
