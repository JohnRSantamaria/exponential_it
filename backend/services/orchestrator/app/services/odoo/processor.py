from app.core.patterns.adapter.base import get_provider
from app.core.schemas.enums import ServicesEnum
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.odoo.client import get_or_create_contact_id


async def odoo_process(taggun_data: TaggunExtractedInvoice, company_vat: str):
    odoo_provider = get_provider(
        service=ServicesEnum.ODOO,
        company_vat=company_vat,
    )

    partner_id = await get_or_create_contact_id(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
    )
