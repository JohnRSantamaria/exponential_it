from datetime import datetime, timezone

from app.core.logging import logger

from app.services.odoo.factory import OdooCompanyFactory
from app.services.odoo.secrets import SecretsService
from app.services.odoo.schemas.product import ProductCreateSchema
from app.services.odoo.schemas.supplier import SupplierCreateSchema
from app.services.odoo.schemas.partnet_address import AddressCreateSchema
from app.services.odoo.schemas.invoice import InvoiceCreateSchema, InvoiceLineSchema
from app.services.odoo.schemas.enums import CompanyTypeEnum, AddressTypeEnum, TaxUseEnum
from app.services.odoo.operations import (
    create_invoice,
    get_or_create_address,
    get_or_create_product,
    get_or_create_supplier,
    get_tax_id_by_amount,
)


def odoo_process():
    """
    El término "partner" (socio) se refiere a cualquier entidad con la que tu empresa interactúe.
    El término "company" (empresa) representa tu propia compañía.
    """

    odoo_secrets = SecretsService(client_vat="cliente1")
    api_key = odoo_secrets.get_api_key()

    factory = OdooCompanyFactory()
    factory.register_company(
        name="company1",
        url="https://exptest.gest.ozonomultimedia.com",
        db="odooexptest",
        username="jhon.rincon@exponentialit.net",
        api_key=api_key,
    )

    company = factory.get_company("company1")
    logger.debug(f"Company creada")

    # 👤 Crear proveedor (partner)
    supplier_data = SupplierCreateSchema(
        name="Alvifusta",
        vat="B96382718",
        email="alvifusta@alvifusta.com",
        phone="962239022",
        company_type=CompanyTypeEnum.company,
    )
    partner_id = get_or_create_supplier(company, supplier_data)
    logger.debug(f"partner creado : {partner_id}")

    # 🏠 Crear dirección asociada
    address_data = AddressCreateSchema(
        partner_id=partner_id,
        address_name="Bodega Central",
        street="Calle 45A #12-34",
        city="Valencia",
        address_type=AddressTypeEnum.invoice,
        country_id=68,
    )
    address_id = get_or_create_address(company, address_data)
    logger.debug(f"address creada : {address_id}")

    invoice_number = "INV-001"

    tax_id = get_tax_id_by_amount(
        company,
        amount=21.0,
        tax_type=TaxUseEnum.purchase,
        invoice_number=invoice_number,
    )
    logger.debug(f"tax_id creada : {tax_id}")

    product_data = ProductCreateSchema(
        name="Tornillo cabeza hexagonal 5mm",
        default_code="TOR-HEX-5",
        list_price=250.0,
        taxes_id=[tax_id],
    )
    logger.debug(f"product_data creado : {product_data}")

    product_id = get_or_create_product(company, product_data)

    logger.debug(f"Producto creado: {product_id}")

    # 🧾 Crear factura de proveedor
    invoice_data = InvoiceCreateSchema(
        partner_id=partner_id,
        invoice_date=datetime.now(timezone.utc).date(),
        date=datetime.now(timezone.utc).date(),  # Fecha contable
        ref="INV/2025/001",
        payment_reference="INV/2025/001",  # opcional, ya se copia por defecto en schema
        to_check=True,  # ya lo es por defecto
        lines=[
            InvoiceLineSchema(
                product_id=product_id, quantity=2, price_unit=250.0, tax_ids=[tax_id]
            )
        ],
    )

    invoice_id = create_invoice(company, invoice_data)
    logger.debug(f"Factura creada: {invoice_id}")

    return {"address_id": address_id}
