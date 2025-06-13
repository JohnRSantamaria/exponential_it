from app.services.odoo.factory import OdooClientFactory
from app.core.settings import settings
from app.services.odoo.operations import (
    get_or_create_supplier,
    get_or_create_product,
    factura_exists,
    create_invoice,
)


def odoo_process():
    factory = OdooClientFactory()

    factory.register_client(
        name="cliente1",
        url="https://exptest.gest.ozonomultimedia.com",
        db="odooexptest",
        username="jhon.rincon@exponentialit.net",
        api_key=settings.API_KEY_ODOO,
    )

    cliente = factory.get_client("cliente1")

    # 👤 Proveedor
    proveedor_id = get_or_create_supplier(
        cliente,
        name="Proveedor X",
        vat="900123456",  # NIT
        email="contacto@proveedorx.com",
    )

    # 📦 Producto
    producto_id = get_or_create_product(
        cliente, name="Cable HDMI", default_code="HDMI-001", price=50.0
    )

    # 🧾 Factura (verifica por ref externa)
    ref = "FACT-INV-789"
    factura_id = factura_exists(cliente, ref)
    if not factura_id: 
        factura_id = create_invoice(
            cliente,
            partner_id=proveedor_id,
            product_id=producto_id,
            quantity=2,
            price_unit=50.0,
            reference=ref,
        )

    return {"factura_id": factura_id}
