from aiohttp import Payload
from app.core.patterns.adapter.odoo_adapter import OdooAdapter
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from exponential_core.odoo import SupplierCreateSchema, AddressCreateSchema
from exponential_core.odoo import CompanyTypeEnum, AddressTypeEnum


async def get_or_create_contact_id(
    odoo_provider: OdooAdapter,
    taggun_data: TaggunExtractedInvoice,
) -> int:

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

    return await odoo_provider.create_vendor(payload=payload)


async def get_or_create_address(
    odoo_provider: OdooAdapter,
    taggun_data: TaggunExtractedInvoice,
    partner_id: int,
):
    payload = AddressCreateSchema(
        address_name=taggun_data.partner_name,
        partner_id=partner_id,
        street=taggun_data.address.street,
        city=taggun_data.address.city,
        address_type=AddressTypeEnum.invoice,
        zip=taggun_data.address.postal_code,
        phone=taggun_data.address.phone,
    )

    return await odoo_provider.create_address(payload=payload)


async def get_tax_id_by_amount(
    odoo_provider: OdooAdapter,
    taggun_data: TaggunExtractedInvoice,
):

    return await odoo_provider.get_tax_id()
