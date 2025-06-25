import json

from typing import List
from fastapi import UploadFile
from pydantic import TypeAdapter
from app.core.settings import settings
from app.core.logging import logger
from app.core.client_provider import ProviderConfig
from app.core.patterns.adapter.zoho_adapter import ZohoAdapter
from app.services.openai.client import OpenAIService
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.zoho.builders import create_bill_payload, create_contact_payload
from app.services.zoho.exceptions import ContactIdNotFoundError
from app.services.zoho.schemas.bills_response import BillsResponse
from app.services.zoho.schemas.chart_of_accounts_response import ChartOfAccountsResponse
from app.services.zoho.schemas.contacts_response import ContactResponse
from app.services.zoho.schemas.taxes_response import TaxesResponse
from app.services.zoho.tax_resolver import calculate_tax_percentage_candidates


async def get_or_create_contact_id(
    zoho_provider: ZohoAdapter, taggun_data: TaggunExtractedInvoice
):
    """Busca un proveedor por CIF o lo crea si no existe, retornando el contact_id."""
    raw_contacts = await zoho_provider.get_all_contacts()

    contacts = [
        {
            "contact_id": raw_contact.get("contact_id", None),
            "contact_name": raw_contact.get("contact_name", None),
            "status": raw_contact.get("status", None),
            "cf_cif": raw_contact.get("cf_cif", None),
        }
        for raw_contact in raw_contacts
    ]

    validated_contacts: List[ContactResponse] = TypeAdapter(
        List[ContactResponse]
    ).validate_python(contacts)

    for validated_contact in validated_contacts:
        if (
            validated_contact.cf_cif == taggun_data.partner_vat
            and validated_contact.is_active
        ):
            return validated_contact.contact_id

    logger.debug(f"No encontro un proveedor con vat {taggun_data.partner_vat}")

    payload = create_contact_payload(taggun_data)
    respose = await zoho_provider.create_vendor(payload=payload)

    contact_id = respose.get("contact_id", None)
    if not contact_id:
        raise ContactIdNotFoundError()

    return contact_id


async def get_or_create_bill(
    zoho_provider: ZohoAdapter,
    taggun_data: TaggunExtractedInvoice,
    partner_id: str,
    file: UploadFile,
    file_content: bytes,
):
    """Busca un bill_id usando el vendor id y el bill numeber si no existe lo crea."""
    raw_bills = await zoho_provider.get_all_bills()
    bills = [
        {
            "bill_id": raw_bill.get("bill_id", None),
            "bill_number": raw_bill.get("bill_number", None),
            "vendor_id": raw_bill.get("vendor_id", None),
        }
        for raw_bill in raw_bills
    ]
    validated_bills: List[BillsResponse] = TypeAdapter(
        List[BillsResponse]
    ).validate_python(bills)

    logger.debug(f"partner_id : {partner_id}")
    logger.debug(f"bill_number : {taggun_data.invoice_number}")

    for validated_bill in validated_bills:
        if (
            validated_bill.vendor_id == partner_id
            and validated_bill.bill_number == taggun_data.invoice_number
        ):
            return validated_bill

    with open("bill.json", "w", encoding="utf-8") as f:
        json.dump(raw_bills, f, ensure_ascii=False, indent=4)

    logger.debug(
        f"No se encontraron facturas con el numero : {taggun_data.invoice_number} "
    )

    # ---------- Obtener el Tax_ID factura ------------------
    raw_taxes = await zoho_provider.get_all_taxes()
    taxes = [
        {
            "tax_id": raw_tax.get("tax_id", None),
            "tax_percentage": raw_tax.get("tax_percentage", 0),
            "tax_account_id": raw_tax.get("tax_account_id", None),
            "status": raw_tax.get("status", None),
        }
        for raw_tax in raw_taxes
    ]

    validated_taxes: List[TaxesResponse] = TypeAdapter(
        List[TaxesResponse]
    ).validate_python(taxes)

    logger.debug(f" amount_tax : {taggun_data.amount_tax}")
    logger.debug(f" amount_total : {taggun_data.amount_total}")
    logger.debug(f" amount_untaxed :{taggun_data.amount_untaxed}")

    candidate_set = calculate_tax_percentage_candidates(
        amount_tax=taggun_data.amount_tax,
        amount_total=taggun_data.amount_total,
        amount_untaxed=taggun_data.amount_untaxed,
    )
    candidates = list(candidate_set)
    logger.debug(f" candidates :{candidates}")

    matching_tax = next(
        (tax for tax in validated_taxes if tax.tax_percentage in candidate_set), None
    )
    tax_id = matching_tax.tax_id

    # --------------- Obtener la clasificación para el tipo de cuenta -----------------
    config = ProviderConfig(
        server_url=settings.URL_OPENAPI,
        api_prefix="/api",
    )
    openai_service = OpenAIService(config=config)

    raw_chart_of_accounts = await zoho_provider.get_chart_of_accounts()

    chart_of_accounts = [
        {
            "account_id": raw_chart_of_account.get("account_id", None),
            "account_name": raw_chart_of_account.get("account_name", None),
            "description": raw_chart_of_account.get("description", None),
            "account_type": raw_chart_of_account.get("account_type", None),
            "is_active": raw_chart_of_account.get("is_active", True),
        }
        for raw_chart_of_account in raw_chart_of_accounts
    ]

    validated_chart_of_accounts: List[ChartOfAccountsResponse] = TypeAdapter(
        List[ChartOfAccountsResponse]
    ).validate_python(chart_of_accounts)

    items = [
        f"{line.quantity} x {line.name} a {line.unit_price} €"
        for line in taggun_data.line_items
    ]

    text = f"El comercio: {taggun_data.partner_name} con los ítems: {', '.join(items)}"

    accounts_dict_list = [
        account.model_dump() for account in validated_chart_of_accounts
    ]
    accounts_json = json.dumps(accounts_dict_list, ensure_ascii=False)

    accounting_account = await openai_service.classify_expense(
        text=text,
        accounts=accounts_json,
    )

    logger.debug(f" accounting_account :{accounting_account}")

    # ------- Creacion de la factura -----------------
    payload = create_bill_payload(
        partner_id=partner_id,
        taggun_data=taggun_data,
        account_id=accounting_account.account_id,
        tax_id=tax_id,
    )

    raw_bill = await zoho_provider.create_bill(payload=payload)
    bill = {
        "bill_id": raw_bill.get("bill_id", None),
        "bill_number": raw_bill.get("bill_number", None),
        "vendor_id": raw_bill.get("vendor_id", None),
    }

    validated_bill = BillsResponse(**bill)

    # --- Attach a la factura. ------------
    await zoho_provider.attach_file_to_bill(
        bill_id=validated_bill.bill_id,
        file=file,
        file_content=file_content,
    )
