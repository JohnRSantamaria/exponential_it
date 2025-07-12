from datetime import datetime
from app.core.logging import logger
from app.services.odoo.client import AsyncOdooClient
from app.services.odoo.utils.cleanner import clean_enum_payload, parse_to_date

from exponential_core.odoo import ProductCreateSchemaV18, InvoiceCreateSchema


async def get_or_create_product(
    company: AsyncOdooClient, product_data: ProductCreateSchemaV18
):
    domain = [["name", "=", product_data.name]]
    if product_data.default_code:
        domain.append(["default_code", "=", product_data.default_code])

    existing = await company.read("product.product", domain, fields=["id"])
    if existing:
        logger.debug(f"Producto ya existente: {existing[0]["id"]}")
        return existing[0]["id"]

    payload = clean_enum_payload(product_data.model_dump(exclude_none=True))
    logger.debug(f"Producto creado {product_data.name}")
    return await company.create("product.product", payload)


async def get_or_create_invoice(
    company: AsyncOdooClient, invoice_data: InvoiceCreateSchema
) -> int:
    """
    Crea o devuelve una factura de proveedor (move_type='in_invoice') si ya existe.
    Se considera duplicada si coincide `ref` (número de factura) y `partner_id`.
    """

    # Verificar si ya existe
    domain = [
        ["move_type", "=", "in_invoice"],
        ["ref", "=", invoice_data.ref],  # Número de factura del proveedor
        ["partner_id", "=", invoice_data.partner_id],
    ]

    existing = await company.read("account.move", domain, fields=["id"])
    if existing:
        logger.debug(f"Factura ya existente: {existing[0]["id"]}")
        return existing[0]["id"]

    # Crear si no existe
    logger.debug(f"Creando factura")
    payload = invoice_data.as_odoo_payload()

    if "invoice_date" in payload and isinstance(payload["invoice_date"], datetime):
        payload["invoice_date"] = parse_to_date(payload.get("invoice_date"))
    if "date" in payload and isinstance(payload["date"], datetime):
        payload["date"] = parse_to_date(payload.get("date"))

    return await company.create("account.move", payload)
