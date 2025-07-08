from fastapi import APIRouter, Body, Depends, File, UploadFile

from app.api.dependencies import get_client_vat
from app.services.zoho.schemas.create_bill import CreateZohoBillRequest
from app.services.zoho.schemas.create_contact import CreateZohoContactRequest
from app.services.zoho.client import zoho_get, zoho_get_all, zoho_post, zoho_post_file


router = APIRouter(prefix="/books", tags=["books"])


@router.get("/organizations")
async def get_all_organizations(company_vat: str = Depends(get_client_vat)):
    return await zoho_get_all(path="/books/v3/organizations", company_vat=company_vat)


@router.get("/contacts", name="Get all contacs")
async def get_all_contacts(company_vat: str = Depends(get_client_vat)):
    return await zoho_get_all(
        path="/books/v3/contacts",
        company_vat=company_vat,
        include_org=True,
    )


@router.get("/settings", name="Get settings")
async def get_settings(company_vat: str = Depends(get_client_vat)):
    return await zoho_get(
        path="/books/v3/settings/customfields?module=contacts",
        company_vat=company_vat,
        include_org=True,
    )


@router.get("/bills", name="Get all bills")
async def get_all_bills(company_vat: str = Depends(get_client_vat)):
    return await zoho_get_all(
        path="/books/v3/bills",
        company_vat=company_vat,
        include_org=True,
    )


@router.post("/bill", name="Create Bill")
async def create_bill(
    bill: CreateZohoBillRequest = Body(...),
    company_vat: str = Depends(get_client_vat),
):
    return await zoho_post(
        path="/books/v3/bills",
        data=bill.clean_payload(),
        company_vat=company_vat,
        include_org=True,
    )


@router.get("/taxes")
async def get_all_taxes(company_vat: str = Depends(get_client_vat)):
    return await zoho_get_all(
        path="/books/v3/settings/taxes",
        company_vat=company_vat,
        include_org=True,
    )


@router.post("/contact")
async def create_contac(
    contact: CreateZohoContactRequest,
    company_vat: str = Depends(get_client_vat),
):
    return await zoho_post(
        "/books/v3/contacts",
        data=contact.clean_payload(),
        company_vat=company_vat,
        include_org=True,
    )


@router.get("/chart-of-accounts")
async def get_all_chartofaccounts(company_vat: str = Depends(get_client_vat)):
    return await zoho_get_all(
        path="/books/v3/chartofaccounts",
        company_vat=company_vat,
        include_org=True,
    )


@router.post("/bill/{bill_id}/attachment", name="Attach file to Bill")
async def attach_bill_file(
    bill_id: str,
    file: UploadFile = File(...),
    company_vat: str = Depends(get_client_vat),
):
    return await zoho_post_file(
        path=f"/books/v3/bills/{bill_id}/attachment",
        file=file,
        company_vat=company_vat,
        include_org=True,
    )


@router.get("/currencies")
async def get_all_currencies(company_vat: str = Depends(get_client_vat)):
    return await zoho_get_all(
        path=f"/books/v3/settings/currencies",
        company_vat=company_vat,
        include_org=True,
    )
