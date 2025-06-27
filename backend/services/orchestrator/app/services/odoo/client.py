from app.core.patterns.adapter.odoo_adapter import OdooAdapter
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from exponential_core.odoo import SupplierCreateSchema
from exponential_core.odoo import CompanyTypeEnum


async def get_or_create_contact_id(
    odoo_provider: OdooAdapter,
    taggun_data: TaggunExtractedInvoice,
):

    payload = SupplierCreateSchema(
        name=taggun_data.partner_name,
        vat=taggun_data.partner_vat,
        email=taggun_data.address.email,
        phone=taggun_data.address.phone,
        company_type=CompanyTypeEnum.company,
        is_company=True,
        street=taggun_data.address.street,
        zip=taggun_data.address.postal_code,
        city=taggun_data.address.city,
        website=taggun_data.address.website,
    )
    await odoo_provider.create_vendor(payload=payload)
