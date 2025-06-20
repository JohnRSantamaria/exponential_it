from fastapi import APIRouter, Body, File, UploadFile

from app.services.zoho.schemas.create_bill import CreateZohoBillRequest
from app.services.zoho.schemas.create_contact import CreateZohoContactRequest
from app.services.zoho.client import zoho_get, zoho_get_all, zoho_post, zoho_post_file


router = APIRouter(prefix="/books", tags=["books"])


@router.get("/organizations")
async def get_all_organizations():
    return await zoho_get_all("/books/v3/organizations")


@router.get("/contacts", name="Get all contacs")
async def get_all_contacts():
    return await zoho_get_all("/books/v3/contacts", include_org=True)


@router.get("/settings", name="Get settings")
async def get_settings():
    return await zoho_get(
        "/books/v3/settings/customfields?module=contacts", include_org=True
    )


@router.get("/bills", name="Get all bills")
async def get_all_bills():
    return await zoho_get_all("/books/v3/bills", include_org=True)


@router.post("/bill", name="Create Bill")
async def create_bill(bill: CreateZohoBillRequest = Body(...)):
    return await zoho_post(
        "/books/v3/bills", data=bill.clean_payload(), include_org=True
    )


@router.get("/taxes")
async def get_all_taxes():
    return await zoho_get_all("/books/v3/settings/taxes", include_org=True)


@router.post("/contact")
async def create_contac(
    contact: CreateZohoContactRequest,
):
    return await zoho_post(
        "/books/v3/contacts", data=contact.clean_payload(), include_org=True
    )


@router.get("/chart-of-accounts")
async def get_all_chartofaccounts():
    return await zoho_get_all("/books/v3/chartofaccounts", include_org=True)


@router.post("/bill/{bill_id}/attachment", name="Attach file to Bill")
async def attach_bill_file(
    bill_id: str,
    file: UploadFile = File(...),
):
    return await zoho_post_file(
        f"/books/v3/bills/{bill_id}/attachment", file, include_org=True
    )


@router.get("/currencies")
async def get_all_currencies():
    return await zoho_get_all(f"/books/v3/settings/currencies", include_org=True)
