def get_or_create_supplier(cliente, name, vat, email=None):
    existing = cliente.read(
        "res.partner", [["name", "=", name], ["vat", "=", vat]], fields=["id"]
    )
    if existing:
        return existing[0]["id"]

    return cliente.create(
        "res.partner",
        {
            "name": name,
            "vat": vat,  # NIT o identificación fiscal
            "supplier_rank": 1,
            "email": email,
            "company_type": "company",
        },
    )


def get_or_create_product(cliente, name, default_code=None, price=0.0):
    domain = [["name", "=", name]]
    if default_code:
        domain.append(["default_code", "=", default_code])

    existing = cliente.read("product.product", domain, fields=["id"])
    if existing:
        return existing[0]["id"]

    return cliente.create(
        "product.product",
        {
            "name": name,
            "list_price": price,
            "default_code": default_code or "",
            "type": "consu",  # puede ser 'service', 'consu', 'product'
        },
    )


def factura_exists(cliente, reference):
    facturas = cliente.read(
        "account.move",
        [["ref", "=", reference], ["move_type", "=", "in_invoice"]],
        fields=["id"],
    )
    return facturas[0]["id"] if facturas else None


def create_invoice(cliente, partner_id, product_id, quantity, price_unit, reference):
    return cliente.create(
        "account.move",
        {
            "move_type": "in_invoice",
            "partner_id": partner_id,
            "ref": reference,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product_id,
                        "quantity": quantity,
                        "price_unit": price_unit,
                        "name": f"{quantity}x Producto",
                    },
                )
            ],
        },
    )
