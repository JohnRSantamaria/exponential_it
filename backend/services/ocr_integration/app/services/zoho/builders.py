from typing import List
from app.services.ocr.schemas import Invoice, Supplier
from app.services.zoho.schemas.create_bill import (
    CreateZohoBillRequest,
    LineItem as ZohoLineItem,
)
from app.services.zoho.schemas.create_contact import (
    CreateZohoContactRequest,
    Address as ZohoAddress,
    CustomFieldInput,
)


def build_zoho_contact_payload(supplier: Supplier) -> CreateZohoContactRequest:
    return CreateZohoContactRequest(
        contact_name=supplier.name,
        company_name=supplier.name,
        website=supplier.website,
        language_code="es",
        contact_type="vendor",
        currency_code="EUR",
        currency_id="6421233000000000109",
        customer_sub_type="business",
        billing_address=ZohoAddress(
            address=supplier.address.street,
            city=supplier.address.city,
            state=supplier.address.state,
            zip=supplier.address.postal_code,
            country=supplier.address.country_code,
            phone=supplier.phone,
            fax=supplier.fax,
        ),
        custom_fields=[
            CustomFieldInput(
                label="CIF",
                value=supplier.vat,
                customfield_id="6421233000000093205",
            )
        ],
    )


def build_zoho_invoice_payload(invoice: Invoice) -> CreateZohoBillRequest:
    invoice_lines = invoice.invoice_lines
    line_items: List[ZohoLineItem] = []

    for line in invoice_lines:
        line_items.append(
            ZohoLineItem(
                name=line.product_name,
                quantity=line.quantity,
                rate=line.price_unit,
                account_id=invoice.account_category.account_id,
                tax_id=line.tax_id,
            )
        )

    return CreateZohoBillRequest(
        vendor_id=invoice.partner_id,
        bill_number=invoice.invoice_origin,
        date=invoice.date_invoice,
        tax_total=invoice.amount_tax,
        sub_total=invoice.amount_untaxed,
        total=invoice.amount_total,
        line_items=line_items,
        notes="Factura generada automáticamente por OCR",
    )
