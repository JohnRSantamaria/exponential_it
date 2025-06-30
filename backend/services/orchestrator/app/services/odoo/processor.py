from app.core.patterns.adapter.base import get_provider
from app.core.schemas.enums import ServicesEnum
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.odoo.client import get_or_create_address, get_or_create_contact_id, get_tax_id_by_amount
from app.core.logging import logger


async def odoo_process(taggun_data: TaggunExtractedInvoice, company_vat: str):
    odoo_provider = get_provider(
        service=ServicesEnum.ODOO,
        company_vat=company_vat,
    )
    logger.debug("Proceso iniciado en ODOO")

    partner_id = await get_or_create_contact_id(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
    )
    logger.debug(f"Company creada exitosamente : {partner_id}")

    address_id = await get_or_create_address(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
        partner_id=partner_id,
    )
    logger.debug(f"Dirección asociada exitosamente : {address_id}")

    tax_id = await get_tax_id_by_amount(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
    )
