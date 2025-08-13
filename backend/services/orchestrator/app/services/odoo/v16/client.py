import json
from typing import List
from fastapi import UploadFile
from pydantic import TypeAdapter
from datetime import datetime
from app.core.logging import logger
from app.core.patterns.adapter.odoo_adapter import OdooAdapter

from app.services.openai.client import OpenAIService
from app.services.odoo.exceptions import OdooTaxIdNotFound
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.openai.schemas.classification_tax_request import (
    ClasificacionRequest,
    TaxIdResponseSchema,
)


from exponential_core.odoo import (
    SupplierCreateSchema,
    AddressCreateSchema,
    ResponseTaxesSchema,
    CompanyTypeEnum,
    AddressTypeEnum,
    ProductCreateSchema,
    ProductTypeEnum,
    InvoiceLineSchema,
    InvoiceCreateSchema,
)


async def get_or_create_contact_id(
    odoo_provider: OdooAdapter,
    taggun_data: TaggunExtractedInvoice,
) -> int:

    payload = SupplierCreateSchema(
        name=taggun_data.partner_name,
        vat=taggun_data.partner_vat,
        email=taggun_data.address.email,
        phone=taggun_data.address.phone,
        company_type=CompanyTypeEnum.COMPANY,
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
        address_type=AddressTypeEnum.INVOICE,
        zip=taggun_data.address.postal_code,
        phone=taggun_data.address.phone,
    )

    return await odoo_provider.create_address(payload=payload)


async def get_validated_tax_ids(
    odoo_provider: OdooAdapter,
) -> List[ResponseTaxesSchema]:
    """ """

    raw_taxes = await odoo_provider.get_all_taxes()

    return TypeAdapter(List[ResponseTaxesSchema]).validate_python(raw_taxes)


async def get_tax_id_openai(
    taggun_data: TaggunExtractedInvoice,
    validated_tax_ids: List[ResponseTaxesSchema],
    openai_service: OpenAIService,
):
    candidates_set = taggun_data.tax_canditates
    logger.debug(f"Candidatos a porcentaje de impuesto: {candidates_set}")

    proveedor = taggun_data.partner_name
    nif = taggun_data.partner_vat
    productos = taggun_data.line_items
    iva_rate = next(iter(candidates_set), None)
    candidate_tax_ids = validated_tax_ids

    if iva_rate is None:
        raise OdooTaxIdNotFound()

    payload = {
        "provider": proveedor,
        "nif": nif,
        "products": [
            item.model_dump(mode="json", exclude_none=True) for item in productos
        ],
        "iva_rate": iva_rate,
        "candidate_tax_ids": [
            item.model_dump(mode="json", exclude_none=True)
            for item in candidate_tax_ids
        ],
    }

    payload = ClasificacionRequest(**payload)

    tax_raw_response = await openai_service.classify_odoo_tax_id(payload)
    try:
        tax_response = TaxIdResponseSchema(**tax_raw_response)
    except Exception as e:
        raise OdooTaxIdNotFound(message=f"Error al identificar el tax id en OpenAi{e}")

    tax_id_number = tax_response.tax_id_number
    if tax_id_number <= 0:
        raise OdooTaxIdNotFound(
            message=f"Error al identificar el tax id en OpenAi",
            data={"tax_id_number": tax_id_number},
        )

    logger.debug(f"Tax ID encontrada id: {tax_id_number}, {tax_response.description}")

    return tax_response.tax_id_number


async def get_tax_id_odoo(
    taggun_data: TaggunExtractedInvoice,
    odoo_provider: OdooAdapter,
    openai_service: OpenAIService,
) -> int:
    validated_tax_ids = await get_validated_tax_ids(
        odoo_provider=odoo_provider,
    )

    return await get_tax_id_openai(
        taggun_data=taggun_data,
        validated_tax_ids=validated_tax_ids,
        openai_service=openai_service,
    )


async def get_or_create_products(
    taggun_data: TaggunExtractedInvoice, odoo_provider: OdooAdapter, tax_id: int
) -> list[InvoiceLineSchema]:
    line_items = taggun_data.line_items
    InvoiceLines: InvoiceLineSchema = []

    for item in line_items:
        payload = ProductCreateSchema(
            name=item.name,
            list_price=item.unit_price,
            detailed_type=ProductTypeEnum.CONSU,
            taxes_id=[tax_id],
        )
        product_id = await odoo_provider.create_product(payload=payload)

        InvoiceLines.append(
            InvoiceLineSchema(
                product_id=product_id,
                price_unit=item.unit_price,
                quantity=item.quantity,
                tax_ids=[tax_id],
            )
        )

    return InvoiceLines


async def get_or_create_invoice(
    taggun_data: TaggunExtractedInvoice,
    odoo_provider: OdooAdapter,
    product_ids: list[InvoiceLineSchema],
    partner_id: int,
):
    payload = InvoiceCreateSchema(
        partner_id=partner_id,
        ref=taggun_data.invoice_number,
        payment_reference=taggun_data.invoice_number,
        invoice_date=taggun_data.date,
        date=datetime.now(),
        to_check=True,
        lines=product_ids,
    )

    return await odoo_provider.create_bill(payload=payload)


async def get_or_attach_document(
    invoice_id: str,
    odoo_provider: OdooAdapter,
    file: UploadFile,
    file_content: bytes,
):

    await odoo_provider.attach_file_to_bill(
        bill_id=invoice_id,
        file=file,
        file_content=file_content,
    )


async def get_final_total_odoo(
    invoice_id: str,
    odoo_provider: OdooAdapter,
):
    return await odoo_provider.get_the_total_of_the_final_invoice(invoice_id=invoice_id)


async def delete_invoice(
    invoice_id: str,
    odoo_provider: OdooAdapter,
):
    return await odoo_provider.delete_final_invoice(invoice_id=invoice_id)
