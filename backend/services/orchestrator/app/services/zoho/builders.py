from app.core.logging import logger
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.zoho.schemas.create_bill import CreateZohoBillRequest, LineItem
from app.services.zoho.schemas.create_contact import (
    CreateZohoContactRequest,
    Address,
    CustomFieldInput,
)


def create_contact_payload(taggun_data: TaggunExtractedInvoice):
    return CreateZohoContactRequest(
        contact_name=taggun_data.partner_name,
        company_name=taggun_data.partner_name,
        language_code="es",
        contact_type="vendor",
        currency_code="EUR",
        currency_id="6421233000000000109",
        customer_sub_type="business",
        billing_address=Address(
            address=taggun_data.address.street,
            city=taggun_data.address.city,
            state=taggun_data.address.state,
            zip=taggun_data.address.postal_code,
            country=taggun_data.address.country_code,
            phone=taggun_data.address.phone,
            fax=taggun_data.address.fax,
        ),
        custom_fields=[
            CustomFieldInput(
                label="CIF",
                value=taggun_data.partner_vat,
                customfield_id="6421233000000093205",
            )
        ],
    )


def create_bill_payload(
    taggun_data: TaggunExtractedInvoice,
    partner_id: str,
    account_id: str,
    tax_id: str,
):

    logger.debug(f" invoice_number : {taggun_data.invoice_number}")

    line_items = [
        LineItem(
            name="Conglomerado de todos los servicios",
            quantity=1,
            rate=taggun_data.amount_untaxed,
            account_id=account_id,
            tax_id=tax_id,
        )
    ]

    return CreateZohoBillRequest(
        vendor_id=partner_id,
        bill_number=taggun_data.invoice_number,
        date=taggun_data.date,
        tax_total=taggun_data.amount_tax,
        sub_total=taggun_data.amount_untaxed,
        total=taggun_data.amount_total,
        line_items=line_items,
        notes="Factura generada automáticamente por OCR",
    )
