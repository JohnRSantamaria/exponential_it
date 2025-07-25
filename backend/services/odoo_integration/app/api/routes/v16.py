from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_company
from app.services.odoo.client import AsyncOdooClient
from app.services.odoo.operations import (
    get_model_fields,
    get_or_create_address,
    get_or_create_invoice,
    get_or_create_product,
    get_or_create_supplier,
    get_required_fields,
    get_tax_id_by_amount,
    get_tax_ids,
)

from exponential_core.odoo import (
    TaxUseEnum,
    InvoiceCreateSchema,
    AddressCreateSchema,
    ProductCreateSchema,
    SupplierCreateSchema,
)


router = APIRouter(prefix="/v16", tags=["v16"])


@router.post("/create-supplier")
async def create_supplier(
    supplier_data: SupplierCreateSchema,
    company: AsyncOdooClient = Depends(get_company),
):
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
        tax_type=TaxUseEnum.PURCHASE,
    )
    return {"tax_id": tax_id}


@router.get("/get-all-tax-id")
async def get_all_tax_ids(
    company: AsyncOdooClient = Depends(get_company),
):
    tax_ids = await get_tax_ids(
        company,
    )
    return {"tax_ids": tax_ids}


@router.post("/create-product")
async def create_product(
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
    invoice_id = await get_or_create_invoice(company, invoice_data)
    return {"invoice_id": invoice_id}


@router.get("/model-fields")
async def model_fields(
    company: AsyncOdooClient = Depends(get_company),
    model: str = Query(
        ..., description="Nombre del modelo en Odoo (ej. 'account.move')"
    ),
):
    fields = await get_model_fields(company=company, model=model)
    return {"fields": fields}


@router.get("/required-fields")
async def required_fields(
    company: AsyncOdooClient = Depends(get_company),
    model: str = Query(
        ..., description="Nombre del modelo en Odoo (ej. 'account.move')"
    ),
):
    fields = await get_required_fields(company=company, model=model)
    return {"fields": fields}
