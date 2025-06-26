from datetime import datetime
from app.services.odoo.factory import OdooCompanyFactory
from app.services.odoo.schemas.enums import TaxUseEnum
from app.services.odoo.schemas.invoice import InvoiceCreateSchema
from app.services.odoo.schemas.partnet_address import AddressCreateSchema
from app.services.odoo.schemas.product import ProductCreateSchema
from app.services.odoo.schemas.supplier import SupplierCreateSchema
from app.services.odoo.secrets import SecretsService
from app.services.odoo.utils.cleanner import clean_enum_payload, parse_to_date
from exponential_core.exceptions import TaxIdNotFoundError
from app.core.logging import logger


def get_or_create_supplier(company, supplier_data: SupplierCreateSchema):
    existing = company.read(
        "res.partner",
        [["name", "=", supplier_data.name], ["vat", "=", supplier_data.vat]],
        fields=["id"],
    )
    if existing:
        return existing[0]["id"]

    payload = clean_enum_payload(supplier_data.as_odoo_payload())
    return company.create("res.partner", payload)


def get_or_create_address(company, address_data: AddressCreateSchema):
    domain = [
        ["parent_id", "=", address_data.partner_id],
        ["name", "=", address_data.address_name],
        ["street", "=", address_data.street],
        ["city", "=", address_data.city],
        ["type", "=", address_data.address_type.value],
    ]
    if address_data.country_id:
        domain.append(["country_id", "=", address_data.country_id])

    existing = company.read("res.partner", domain, fields=["id"])
    if existing:
        return existing[0]["id"]

    payload = clean_enum_payload(address_data.as_odoo_payload())
    return company.create("res.partner", payload)


def get_tax_id_by_amount(
    company, amount: float, tax_type: TaxUseEnum, invoice_number: str
) -> int:
    taxes = company.read(
        "account.tax",
        [["type_tax_use", "=", tax_type.value]],
        fields=["id", "amount"],
    )

    candidates = [round(t["amount"], 2) for t in taxes]

    for tax in taxes:
        if round(tax["amount"], 2) == round(amount, 2):
            return tax["id"]

    raise TaxIdNotFoundError(invoice_number=invoice_number, candidates=candidates)


def get_or_create_product(company, product_data: ProductCreateSchema):
    domain = [["name", "=", product_data.name]]
    if product_data.default_code:
        domain.append(["default_code", "=", product_data.default_code])

    existing = company.read("product.product", domain, fields=["id"])
    if existing:
        return existing[0]["id"]

    payload = clean_enum_payload(product_data.model_dump(exclude_none=True))

    return company.create("product.product", payload)


def create_invoice(company, invoice_data: InvoiceCreateSchema) -> int:
    """
    Crea una factura de proveedor (move_type='in_invoice') en Odoo.
    """
    payload = invoice_data.as_odoo_payload()

    # 💡 Normalizamos fechas a objetos date (no datetime, no str)
    if "invoice_date" in payload and isinstance(payload["invoice_date"], datetime):
        payload["invoice_date"] = parse_to_date(payload.get("invoice_date"))
    if "date" in payload and isinstance(payload["date"], datetime):
        payload["date"] = parse_to_date(payload.get("date"))

    return company.create("account.move", payload)


def register_company(client_vat: str):
    # Obtención de paramatros
    secrets = SecretsService(client_vat)
    api_key = secrets.get_api_key()
    url = secrets.get_url()
    db = secrets.get_db()
    username = secrets.get_username()

    factory = OdooCompanyFactory()
    factory.register_company(
        client_vat=client_vat,
        url=url,
        db=db,
        username=username,
        api_key=api_key,
    )

    company = factory.get_company(client_vat=client_vat)
    logger.debug(f"Company creada")
    return company
