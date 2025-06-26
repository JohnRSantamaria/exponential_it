import json

from typing import List, Optional
from fastapi import UploadFile
from pydantic import TypeAdapter
from app.core.settings import settings
from app.core.logging import logger
from app.core.client_provider import ProviderConfig
from app.core.patterns.adapter.zoho_adapter import ZohoAdapter
from app.services.openai.client import OpenAIService
from app.services.openai.schemas.account_category import AccountCategory
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.zoho.builders import create_bill_payload, create_contact_payload
from app.services.zoho.exceptions import ContactIdNotFoundError
from app.services.zoho.schemas.bills_response import BillsResponse
from app.services.zoho.schemas.chart_of_accounts_response import ChartOfAccountsResponse
from app.services.zoho.schemas.contacts_response import ContactResponse
from app.services.zoho.schemas.taxes_response import TaxesResponse
from app.services.zoho.tax_resolver import calculate_tax_percentage_candidates


async def find_contact(
    zoho_provider: ZohoAdapter, taggun_data: TaggunExtractedInvoice
) -> Optional[ContactResponse]:
    """Busca un proveedor en Zoho por su CIF."""
    logger.debug("Buscando proveedor en Zoho")
    raw_contacts = await zoho_provider.get_all_contacts()
    contacts = [
        {
            "contact_id": rc.get("contact_id"),
            "contact_name": rc.get("contact_name"),
            "status": rc.get("status"),
            "cf_cif": rc.get("cf_cif"),
        }
        for rc in raw_contacts
    ]
    validated = TypeAdapter(List[ContactResponse]).validate_python(contacts)

    for contact in validated:
        if contact.cf_cif == taggun_data.partner_vat and contact.is_active:
            logger.debug(f"Proveedor encontrado: {contact.contact_id}")
            return contact.contact_id

    logger.debug(f"Proveedor con vat {taggun_data.partner_vat} no encontrado")
    return None


async def get_or_create_contact_id(
    zoho_provider: ZohoAdapter, taggun_data: TaggunExtractedInvoice
) -> str:
    """Retorna el contact_id si existe o crea el proveedor en Zoho."""
    contact_id = await find_contact(
        zoho_provider=zoho_provider, taggun_data=taggun_data
    )
    if contact_id:
        return contact_id

    logger.debug(f"Creando proveedor con vat {taggun_data.partner_vat}")
    payload = create_contact_payload(taggun_data)
    response = await zoho_provider.create_vendor(payload=payload)

    contact_id = response.get("contact_id")
    if not contact_id:
        raise ContactIdNotFoundError()

    logger.debug(f"Proveedor creado con contact_id: {contact_id}")
    return contact_id


async def find_bill(
    zoho_provider: ZohoAdapter, taggun_data: TaggunExtractedInvoice, partner_id: str
) -> Optional[BillsResponse]:
    """Busca una factura en Zoho por vendor_id y número de factura."""
    logger.debug(
        f"Buscando factura número {taggun_data.invoice_number} para vendor {partner_id}"
    )
    raw_bills = await zoho_provider.get_all_bills()
    bills = [
        {
            "bill_id": rb.get("bill_id"),
            "bill_number": rb.get("bill_number"),
            "vendor_id": rb.get("vendor_id"),
        }
        for rb in raw_bills
    ]
    validated = TypeAdapter(List[BillsResponse]).validate_python(bills)

    for bill in validated:
        if (
            bill.vendor_id == partner_id
            and bill.bill_number == taggun_data.invoice_number
        ):
            logger.debug(f"Factura existente encontrada: {bill.bill_id}")
            return bill

    return None


async def get_tax_id(
    zoho_provider: ZohoAdapter, taggun_data: TaggunExtractedInvoice
) -> str:
    """Determina el tax_id adecuado basado en el porcentaje calculado."""
    logger.debug("Calculando tax_id basado en los montos de la factura")
    raw_taxes = await zoho_provider.get_all_taxes()
    taxes = [
        {
            "tax_id": t.get("tax_id"),
            "tax_percentage": t.get("tax_percentage", 0),
            "tax_account_id": t.get("tax_account_id"),
            "status": t.get("status"),
        }
        for t in raw_taxes
    ]
    validated = TypeAdapter(List[TaxesResponse]).validate_python(taxes)

    candidate_set = calculate_tax_percentage_candidates(
        amount_tax=taggun_data.amount_tax,
        amount_total=taggun_data.amount_total,
        amount_untaxed=taggun_data.amount_untaxed,
    )
    logger.debug(f"Candidatos a porcentaje de impuesto: {candidate_set}")

    matching = next(
        (tax for tax in validated if tax.tax_percentage in candidate_set), None
    )
    if matching:
        logger.debug(f"Tax seleccionado: {matching.tax_id}")
        return matching.tax_id
    else:
        logger.warning(
            "No se encontró un tax_id que coincida con los porcentajes calculados"
        )
        return ""


async def classification_for_account(
    zoho_provider: ZohoAdapter, taggun_data: TaggunExtractedInvoice
) -> Optional[AccountCategory]:
    """Clasifica la factura usando OpenAI para obtener el account_id más adecuado."""
    config = ProviderConfig(server_url=settings.URL_OPENAPI, api_prefix="/api")
    openai_service = OpenAIService(config=config)

    logger.debug("Inicia el proceso de claseficación")
    raw_accounts = await zoho_provider.get_chart_of_accounts()
    accounts = [
        {
            "account_id": a.get("account_id"),
            "account_name": a.get("account_name"),
            "description": a.get("description"),
            "account_type": a.get("account_type"),
            "is_active": a.get("is_active", True),
        }
        for a in raw_accounts
    ]
    validated = TypeAdapter(List[ChartOfAccountsResponse]).validate_python(accounts)

    item_text = ", ".join(
        f"{i.quantity} x {i.name} a {i.unit_price} €" for i in taggun_data.line_items
    )
    prompt = f"El comercio: {taggun_data.partner_name} con los ítems: {item_text}"

    result = await openai_service.classify_expense(
        text=prompt,
        accounts=json.dumps([a.model_dump() for a in validated], ensure_ascii=False),
    )

    logger.debug(
        f"Clasificación seleccionada: {result.account_id} - {result.account_name}"
    )
    return result


async def create_bill(
    zoho_provider: ZohoAdapter,
    taggun_data: TaggunExtractedInvoice,
    partner_id: str,
    accounting_account: AccountCategory,
    tax_id: str,
) -> BillsResponse:
    """Crea una factura en Zoho."""
    logger.debug("Creando factura en Zoho")
    payload = create_bill_payload(
        partner_id=partner_id,
        taggun_data=taggun_data,
        account_id=accounting_account.account_id,
        tax_id=tax_id,
    )
    raw = await zoho_provider.create_bill(payload=payload)

    logger.debug(f"Factura creada con ID: {raw.get('bill_id')}")
    return BillsResponse(
        bill_id=raw.get("bill_id"),
        bill_number=raw.get("bill_number"),
        vendor_id=raw.get("vendor_id"),
    )


async def get_or_create_bill(
    zoho_provider: ZohoAdapter,
    taggun_data: TaggunExtractedInvoice,
    partner_id: str,
    file: UploadFile,
    file_content: bytes,
):
    """Busca una factura existente o la crea, luego adjunta el archivo PDF."""
    logger.debug("Iniciando proceso de creación o búsqueda de factura en Zoho")
    bill = await find_bill(
        zoho_provider=zoho_provider, taggun_data=taggun_data, partner_id=partner_id
    )

    if not bill:
        logger.debug("Factura no encontrada, creando nueva factura")
        tax_id = await get_tax_id(zoho_provider=zoho_provider, taggun_data=taggun_data)
        account = await classification_for_account(
            zoho_provider=zoho_provider, taggun_data=taggun_data
        )
        bill = await create_bill(
            zoho_provider=zoho_provider,
            taggun_data=taggun_data,
            partner_id=partner_id,
            accounting_account=account,
            tax_id=tax_id,
        )

        logger.debug(f"Adjuntando archivo a la factura {bill.bill_id}")
        await zoho_provider.attach_file_to_bill(
            bill_id=bill.bill_id,
            file=file,
            file_content=file_content,
        )
        logger.info(f"Proceso completo para factura {bill.bill_id}")
