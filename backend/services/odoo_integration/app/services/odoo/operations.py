from app.services.odoo.schemas.partnet_address import AddressCreateSchema
from app.services.odoo.schemas.supplier import SupplierCreateSchema
from app.services.odoo.utils.cleanner import clean_enum_payload


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
