from fastapi import APIRouter, Depends

from app.api.dependencies import get_client_vat, get_company
from app.services.odoo.client import AsyncOdooClient
from app.services.odoo.operations import (
    get_or_create_address,
    get_or_create_invoice,
    get_or_create_product,
    get_or_create_supplier,
    get_tax_id_by_amount,
)
from app.services.odoo.schemas.enums import TaxUseEnum
from app.services.odoo.schemas.invoice import InvoiceCreateSchema
from app.services.odoo.schemas.partnet_address import AddressCreateSchema
from app.services.odoo.schemas.product import ProductCreateSchema
from app.services.odoo.schemas.supplier import SupplierCreateSchema

router = APIRouter()


@router.post("/create-supplier")
async def create_supplier(
    supplier_data: SupplierCreateSchema,
    company: AsyncOdooClient = Depends(get_company),
    client_vat: str = Depends(get_client_vat),
):
    # 👤 Crear proveedor (partner) B70845755
    if supplier_data.vat != client_vat:
        return {
            "error": "El VAT del proveedor no coincide con el del cliente autenticado.",
            "body_vat": supplier_data.vat,
            "header_vat": client_vat,
        }

    partner_id = await get_or_create_supplier(company, supplier_data)

    return {"partner_id": partner_id}


@router.post("/create-address")
async def create_address(
    address_data: AddressCreateSchema,
    company: AsyncOdooClient = Depends(get_company),
):
    # 🏠 Crear dirección asociada
    address_id = await get_or_create_address(company, address_data)
    return {"address_id": address_id}


@router.get("/get-tax-id")
async def get_tax_id(
    amount: float,
    company: AsyncOdooClient = Depends(get_company),
):
    tax_id = await get_tax_id_by_amount(
        company,
        amount=amount,
        tax_type=TaxUseEnum.purchase,
    )
    return {"tax_id": tax_id}


@router.post("/create-product")
async def crete_produt(
    product_data: ProductCreateSchema,
    company: AsyncOdooClient = Depends(get_company),
):
    product_id = await get_or_create_product(company, product_data)
    return {"product_id": product_id}


@router.post("/register-invoice")
async def register_invoice(
    invoice_data: InvoiceCreateSchema,
    company: AsyncOdooClient = Depends(get_company),
):
    # 🧾 Crear factura de proveedor
    invoice_id = await get_or_create_invoice(company, invoice_data)
    return {"invoice_id": invoice_id}
