from datetime import datetime
from app.core.logging import logger
from app.services.odoo.client import AsyncOdooClient

from app.services.odoo.schemas.invoice import InvoiceCreateSchemaV18
from app.services.odoo.utils.cleanner import clean_enum_payload, parse_to_date
from exponential_core.exceptions import TaxIdNotFoundError
from exponential_core.odoo import (
    TaxUseEnum,
    AddressCreateSchema,
    ProductCreateSchema,
    SupplierCreateSchema,
)


async def get_or_create_supplier(
    company: AsyncOdooClient, supplier_data: SupplierCreateSchema
):
    existing = await company.read(
        "res.partner",
        [["name", "=", supplier_data.name], ["vat", "=", supplier_data.vat]],
        fields=["id"],
    )
    if existing:
        logger.debug(f"Supplier ya existente: {existing[0]["id"]}")
        return existing[0]["id"]

    logger.debug(f"Creando Supplier")
    payload = clean_enum_payload(supplier_data.as_odoo_payload())
    return await company.create("res.partner", payload)


async def get_or_create_address(
    company: AsyncOdooClient, address_data: AddressCreateSchema
):
    domain = [
        ["parent_id", "=", address_data.partner_id],
        ["name", "=", address_data.address_name],
        ["street", "=", address_data.street],
        ["city", "=", address_data.city],
        ["type", "=", address_data.address_type],
    ]
    if address_data.country_id:
        domain.append(["country_id", "=", address_data.country_id])

    existing = await company.read("res.partner", domain, fields=["id"])
    if existing:
        logger.debug(f"Dirección ya existente: {existing[0]["id"]}")
        return existing[0]["id"]

    logger.debug(f"Creando dirección")
    payload = clean_enum_payload(address_data.as_odoo_payload())
    return await company.create("res.partner", payload)


async def get_tax_ids(company: AsyncOdooClient) -> list[dict]:
    taxes = await company.read(
        "account.tax",
        [["type_tax_use", "=", "purchase"]],
        fields=["id", "name", "amount", "type_tax_use", "active"],
    )
    return taxes


async def get_tax_id_by_amount(
    company: AsyncOdooClient,
    amount: float,
    tax_type: TaxUseEnum,
) -> int:
    taxes = await company.read(
        "account.tax",
        [["type_tax_use", "=", tax_type.value]],
        fields=["id", "amount"],
    )

    candidates = [round(t["amount"], 2) for t in taxes]

    for tax in taxes:
        if round(tax["amount"], 2) == round(amount, 2):
            return tax["id"]

    raise TaxIdNotFoundError(invoice_number="", candidates=candidates)


async def get_or_create_product(
    company: AsyncOdooClient, product_data: ProductCreateSchema
):
    domain = [["name", "=", product_data.name]]
    if product_data.default_code:
        domain.append(["default_code", "=", product_data.default_code])

    existing = await company.read("product.product", domain, fields=["id"])
    if existing:
        logger.debug(f"Producto ya existente: {existing[0]["id"]}")
        return existing[0]["id"]

    logger.debug(f"Creando producto")
    payload = clean_enum_payload(product_data.model_dump(exclude_none=True))
    return await company.create("product.product", payload)


async def get_or_create_invoice(
    company: AsyncOdooClient, invoice_data: InvoiceCreateSchemaV18
) -> int:
    """
    Crea o devuelve una factura de proveedor (move_type='in_invoice') si ya existe.
    Se considera duplicada si coincide `ref` (número de factura) y `partner_id`.
    """

    domain = [
        ["move_type", "=", "in_invoice"],
        ["ref", "=", invoice_data.ref],  # Número de factura del proveedor
        ["partner_id", "=", invoice_data.partner_id],
    ]

    existing = await company.read("account.move", domain, fields=["id"])
    if existing:
        logger.debug(f"Factura ya existente: {existing[0]["id"]}")
        return existing[0]["id"]

    logger.debug(f"Creando factura")
    payload = invoice_data.as_odoo_payload()

    if "invoice_date" in payload and isinstance(payload["invoice_date"], datetime):
        payload["invoice_date"] = parse_to_date(payload.get("invoice_date"))
    if "date" in payload and isinstance(payload["date"], datetime):
        payload["date"] = parse_to_date(payload.get("date"))

    return await company.create("account.move", payload)


async def get_model_fields(company: AsyncOdooClient, model: str) -> dict:
    """
    Retorna todos los campos disponibles de un modelo Odoo, incluyendo tipo y etiqueta.

    - model: nombre del modelo Odoo que se desea consultar. Ejemplos comunes:
        - 'res.partner': Representa contactos, proveedores y clientes en Odoo.
        - 'account.tax': Representa los diferentes tipos de impuestos configurados en Odoo.
        - 'product.product': Representa productos (SKU) individuales disponibles para vender o comprar.
        - 'account.move': Representa facturas, asientos contables y otros movimientos financieros.

    Retorna:
        diccionario {nombre_campo: {'type': ..., 'string': ...}}
        Por ejemplo: {'id': {'type': 'integer', 'string': 'ID'}, ...}
    """
    fields = await company.fields_get(model)
    return {
        name: {
            "string": meta["string"],
            "type": meta["type"],
            "help": meta.get("help"),
        }
        for name, meta in fields.items()
    }


async def get_required_fields(company: AsyncOdooClient, model: str) -> dict:
    """
    Retorna un diccionario con la metadata de los campos obligatorios de un modelo Odoo,
    incluyendo tipo y etiqueta.

    - model: nombre del modelo Odoo que se desea consultar. Ejemplos comunes:
        - 'res.partner': Representa contactos, proveedores y clientes en Odoo.
        - 'account.tax': Representa los diferentes tipos de impuestos configurados en Odoo.
        - 'product.product': Representa productos (SKU) individuales disponibles para vender o comprar.
        - 'account.move': Representa facturas, asientos contables y otros movimientos financieros.

    Retorna:
        diccionario {nombre_campo: {'type': ..., 'string': ...}} solo para los campos obligatorios.
        Por ejemplo: {'name': {'type': 'char', 'string': 'Nombre'}, ...}
    """
    fields = await company.fields_get(model)
    return {
        name: {
            "string": meta["string"],
            "type": meta["type"],
            "help": meta.get("help"),
        }
        for name, meta in fields.items()
        if meta.get("required")
    }
