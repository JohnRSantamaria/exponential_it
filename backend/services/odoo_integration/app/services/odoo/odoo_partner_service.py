# app/services/odoo_partner_service.py

import json
from typing import List, Dict
from fastapi.exceptions import RequestValidationError
from odoorpc import ODOO
from odoorpc.models import MetaModel

from app.core.types import CustomAppException


def get_all_partners(odoo: ODOO, limit: int = 20) -> List[Dict]:
    try:
        Partner = odoo.env["res.partner"]
        return Partner.search_read(
            [("customer_rank", ">", 0)],
            ["name", "email", "phone"],
            limit=limit,
        )
    except Exception as e:
        raise RuntimeError(f"Error al obtener partners: {str(e)}")


def get_all_suppliers(odoo: ODOO, limit: int = 20) -> List[Dict]:

    Partner = odoo.env["res.partner"]
    suppliers = Partner.search_read(
        [("supplier_rank", ">", 0)],  # Solo proveedores
        ["name", "email", "phone"],
        limit=limit,
    )
    return suppliers


def create_partner(
    data,
    odoo: ODOO,
) -> dict:
    Partner = odoo.env["res.partner"]

    partner_id = Partner.create(
        {
            "name": "Cliente API",
            "email": "cliente@ejemplo.com",
            "phone": "+57 3000000000",
            "customer_rank": 1,
        }
    )

    return Partner.read(partner_id, ["id", "name", "email", "phone"])[0]


def create_supplier(
    data,
    odoo: ODOO,
) -> dict:

    Partner = odoo.env["res.partner"]

    partner_id = Partner.create(
        {
            "name": "Proveedor API",
            "email": "proveedor@ejemplo.com",
            "phone": "+57 3011234567",
            "supplier_rank": 1,  # Marcar como proveedor
        }
    )

    return Partner.read(partner_id, ["id", "name", "email", "phone"])[0]


def get_currency(odoo: ODOO, code: str) -> int:
    currency_model = odoo.env["res.currency"]

    all_currencies = get_all_currencies(currency_model)

    for currency in all_currencies:
        if str(currency.get("name")).lower().strip() == code.lower().strip():
            return currency.get("id")

    raise CustomAppException(
        status_code=404,
        message=f"La moneda {code} no se encuentra",
    )


def create_draft_invoice(payload: dict, odoo: ODOO) -> dict:
    """"""
    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError()
    except (json.JSONDecodeError, ValueError):
        raise RequestValidationError(
            "El campo 'payload' debe ser un JSON válido con formato de objeto (dict)."
        )

    Invoice = odoo.env["account.move"]
    data = data["properties"]

    currency_code = data["currency_id"]["value"]
    currency_id = get_currency(odoo, code=currency_code)

    # Preparar las líneas de factura
    invoice_lines = []
    for line in data["invoice_line_ids"]["items"]:
        invoice_lines.append(
            (
                0,
                0,
                {
                    "name": line["product_name"],
                    "quantity": line["quantity"],
                    "price_unit": line["price_unit"],
                    "discount": line.get("discount", 0.0),
                    # Puedes añadir tax_ids aquí si están disponibles
                },
            )
        )

    invoice_data = {
        "move_type": "in_invoice",  # Factura de proveedor
        "partner_id": data["partner_id"]["value"],
        "invoice_date": data["date_invoice"]["value"],
        "invoice_date_due": data["date_due"]["value"],
        "currency_id": currency_id,
        "invoice_origin": data["invoice_origin"]["value"],
        "invoice_line_ids": invoice_lines,
        "payment_reference": data["payment_reference"]["value"],
    }

    # Campos opcionales
    if data.get("journal_id") and data["journal_id"]["value"]:
        invoice_data["journal_id"] = data["journal_id"]["value"]
    if data.get("payment_term_id") and data["payment_term_id"]["value"]:
        invoice_data["invoice_payment_term_id"] = data["payment_term_id"]["value"]
    if data.get("company_id") and data["company_id"]["value"]:
        invoice_data["company_id"] = data["company_id"]["value"]

    # Crear factura
    invoice_id = Invoice.create(invoice_data)

    return Invoice.read(invoice_id, ["id", "name", "state", "amount_total"])[0]


def get_all_currencies(currency_model: MetaModel) -> List[Dict]:

    currencies = currency_model.search_read(
        [],  # sin filtros
        ["id", "name", "currency_unit_label", "symbol", "active"],
        limit=1000,
        context={"active_test": False},  # <<< incluir inactivas también
    )
    return currencies
