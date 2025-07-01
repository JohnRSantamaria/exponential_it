from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from app.core.patterns.adapter.base import get_provider
from app.core.schemas.enums import ServicesEnum
from app.services.odoo.secrets import SecretsServiceOdoo
from app.services.openai.client import OpenAIService
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.odoo.client import (
    get_or_create_address,
    get_or_create_contact_id,
    get_tax_id_openai,
    get_validated_tax_ids,
)
from app.core.logging import logger


async def odoo_process(
    taggun_data: TaggunExtractedInvoice,
    company_vat: str,
):
    odoo_provider = get_provider(
        service=ServicesEnum.ODOO,
        company_vat=company_vat,
    )
    config = ProviderConfig(server_url=settings.URL_OPENAPI, api_prefix="/api")
    openai_service = OpenAIService(config=config)

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

    secrets_service = await SecretsServiceOdoo(company_vat=company_vat).load()

    tax_id = secrets_service.get_tax_id()

    if not tax_id:
        validated_tax_ids = await get_validated_tax_ids(
            odoo_provider=odoo_provider,
        )

        tax_id = await get_tax_id_openai(
            taggun_data=taggun_data,
            validated_tax_ids=validated_tax_ids,
            openai_service=openai_service,
        )

    # Create products
