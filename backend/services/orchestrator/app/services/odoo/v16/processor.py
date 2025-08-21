from decimal import ROUND_HALF_UP, Decimal
from fastapi import UploadFile

from app.core.logging import logger
from app.core.schemas.enums import ServicesEnum
from app.core.patterns.adapter.base import get_provider
from app.services.odoo.secrets import SecretsServiceOdoo
from app.services.openai.client import OpenAIService
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.odoo.exceptions import (
    OdooCreationError,
    OdooDeleteError,
    OdooTaxIdNotFound,
)


from app.services.odoo.v16.client import (
    delete_invoice,
    get_final_total_odoo,
    get_or_attach_document,
    get_or_create_address,
    get_or_create_contact_id,
    get_or_create_invoice,
    get_or_create_products,
    get_tax_id_odoo,
    get_withholding,
)


def _to_decimal(x) -> Decimal:
    if x is None:
        return Decimal("0.00")
    if isinstance(x, Decimal):
        return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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

    # Creación y obtención de Tax y retenciones
    tax_canditates = taggun_data.tax_canditates or set()

    withholdings = {t for t in tax_canditates if t < 0}
    taggun_data.tax_canditates -= withholdings  # elimina negativos del set original

    tax_id = await get_tax_id_odoo(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
        openai_service=openai_service,
    )

    withholding_tax_ids: list[int] = []

    for w in sorted(withholdings):
        tax_id_wh = await get_withholding(amount=w, odoo_provider=odoo_provider)
        if tax_id_wh is not None:
            withholding_tax_ids.append(tax_id_wh)

    product_ids = await get_or_create_products(
        taggun_data=taggun_data,
        odoo_provider=odoo_provider,
        tax_id=tax_id,
        withholding_tax_ids=withholding_tax_ids,
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

    # ------- Comparación con tolerancia -------
    tolerance = Decimal("0.05")  # ajusta a tu necesidad

    odoo_total = _to_decimal(response.get("amount_total"))
    parsed_total = _to_decimal(taggun_data.amount_total)

    logger.debug(f"Total en la factura (parseado): {parsed_total}")
    logger.debug(f"Total final en Odoo: {odoo_total}")

    diff = (odoo_total - parsed_total).copy_abs()

    if diff > tolerance:
        logger.warning(
            f"Los totales difieren más que la tolerancia ({diff} > {tolerance}) "
            f"para la factura {file.filename}, se eliminará."
        )
        try:
            await delete_invoice(
                invoice_id=invoice_id,
                odoo_provider=odoo_provider,
            )
            logger.info("Factura eliminada correctamente")
            raise OdooCreationError(
                f"Los totales son diferentes (diff={diff}) para la factura {file.filename}, se eliminó."
            )
        except Exception as e:
            raise OdooDeleteError(message=str(e))
    else:
        if diff > Decimal("0.00"):
            logger.info(
                f"✅ Totales aceptados por tolerancia: diff={diff} ≤ {tolerance}. "
                f"Factura {file.filename} continuará."
            )
        else:
            logger.info("✅ Totales coinciden exactamente.")

    # Adjuntar documento si todo está OK
    await get_or_attach_document(
        invoice_id=invoice_id,
        odoo_provider=odoo_provider,
        file=file,
        file_content=file_content,
    )
