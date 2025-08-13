from fastapi import UploadFile
from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from app.core.patterns.adapter.base import get_provider
from app.core.schemas.enums import ServicesEnum
from app.services.odoo.exceptions import (
    OdooCreationError,
    OdooDeleteError,
    OdooTaxIdNotFound,
)
from app.services.odoo.secrets import SecretsServiceOdoo
from app.services.openai.client import OpenAIService
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.odoo.v16.client import (
    delete_invoice,
    get_final_total_odoo,
    get_or_attach_document,
    get_or_create_address,
    get_or_create_contact_id,
    get_or_create_invoice,
    get_or_create_products,
    get_tax_id_odoo,
)
from app.core.logging import logger

from exponential_core.exceptions import CustomAppException


async def odoo_process(
    file: UploadFile,
    file_content: bytes,
    taggun_data: TaggunExtractedInvoice,
    company_vat: str,
    openai_service: OpenAIService,
):

    odoo_provider = get_provider(
        service=ServicesEnum.ODOO,
        company_vat=company_vat,
        version="v16",
    )

    # Verificación invoice_number
    invoice_number = taggun_data.invoice_number
    partner_name = taggun_data.partner_name
    if not invoice_number:
        cif = await openai_service.search_cif_by_partner(partner_name=partner_name)
        cif = cif.get("CIF", "0")
        if cif == "0":
            raise OdooTaxIdNotFound()
        else:
            taggun_data.invoice_number = cif

    # Creación del proveedor
    logger.info("Creando u obteniendo al proveedor.")
    partner_id = await get_or_create_contact_id(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
    )
    logger.info(f"Proveedor obtenido con éxito : {partner_id}")

    # Creación de la dirreción
    logger.info("Creando u obteniendo la dirección de facturación.")
    address_id = await get_or_create_address(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
        partner_id=partner_id,
    )
    logger.debug(f"Dirección obtenida con éxito : {address_id}")

    secrets_service = await SecretsServiceOdoo(company_vat=company_vat).load()

    tax_id = secrets_service.get_tax_id()

    if not tax_id:
        tax_id = await get_tax_id_odoo(
            taggun_data=taggun_data,
            odoo_provider=odoo_provider,
            openai_service=openai_service,
        )

    product_ids = await get_or_create_products(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
        tax_id=tax_id,
    )

    invoice_id = await get_or_create_invoice(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
        product_ids=product_ids,
        partner_id=partner_id,
    )

    response = await get_final_total_odoo(
        odoo_provider=odoo_provider, invoice_id=invoice_id
    )

    amount_total = response.get("amount_total")

    if amount_total and amount_total != taggun_data.amount_total:
        logger.debug(f"Total en la factura: {taggun_data.amount_total}")
        logger.debug(f"Total final: {amount_total}")
        logger.warning(
            f"Los totales son diferentes para la factura {file.filename}, se eliminara."
        )

        try:
            await delete_invoice(
                invoice_id=invoice_id,
                odoo_provider=odoo_provider,
            )
            logger.info("Factura eliminada correctamente")

            raise OdooCreationError(
                f"Los totales son diferentes para la factura {file.filename}, se elimino."
            )
        except Exception as e:
            raise OdooDeleteError(message=str(e))

    await get_or_attach_document(
        invoice_id=invoice_id,
        odoo_provider=odoo_provider,
        file=file,
        file_content=file_content,
    )
