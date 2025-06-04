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
        email=supplier.email,
        phone=supplier.phone,
    )


def build_zoho_invoice_payload(invoice: Invoice) -> CreateZohoBillRequest:
    return CreateZohoBillRequest()
