from fastapi import APIRouter, Depends

from app.api.dependencies import get_client_vat, get_company
from app.core.logging import logger
from app.services.odoo.factory import OdooCompanyFactory
from app.services.odoo.operations import get_or_create_supplier
from app.services.odoo.schemas.enums import CompanyTypeEnum
from app.services.odoo.schemas.supplier import SupplierCreateSchema

router = APIRouter()


@router.post("/")
def entry(
    company: OdooCompanyFactory = Depends(get_company),
    client_vat: str = Depends(get_client_vat),
):
    supplier_data = SupplierCreateSchema(
        name="Alvifusta",
        vat=client_vat,
        email="alvifusta@alvifusta.com",
        phone="962239022",
        company_type=CompanyTypeEnum.company,
    )
    partner_id = get_or_create_supplier(company, supplier_data)

    return {"partner_id": partner_id}
