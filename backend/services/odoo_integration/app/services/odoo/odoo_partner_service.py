# app/services/odoo_partner_service.py

from typing import List, Dict
from odoorpc import ODOO


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


def create_draft_invoice(data, odoo: ODOO) -> dict:

    Invoice = odoo.env["account.move"]

    invoice_id = Invoice.create(
        {
            "move_type": "out_invoice",
            "partner_id": 11,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Servicio de consultoría",
                        "quantity": 1,
                        "price_unit": 500,
                    },
                ),
                (0, 0, {"name": "Licencia anual", "quantity": 2, "price_unit": 200}),
            ],
        }
    )

    return Invoice.read(invoice_id, ["id", "name", "state", "amount_total"])[0]
