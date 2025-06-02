from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies import required_service
from app.core.exceptions.types import CustomAppException
from app.services.admin.schemas import UserDataSchema
from app.services.zoho.client import zoho_get, zoho_get_all, zoho_post, zoho_post_file


router = APIRouter(prefix="/books", tags=["books"])


@router.get("/organizations")
async def get_all_organizations(
    _: UserDataSchema = Depends(required_service(["1"])),
):
    return await zoho_get_all("/books/v3/organizations")


@router.get("/contacts", name="Get all contacs")
async def get_all_contacts(
    _: UserDataSchema = Depends(required_service(["1"])),
):
    return await zoho_get_all("/books/v3/contacts", include_org=True)


@router.get("/settings", name="Get settings")
async def get_settings(
    _: UserDataSchema = Depends(required_service(["1"])),
):
    return await zoho_get(
        "/books/v3/settings/customfields?module=contacts", include_org=True
    )


@router.get("/bills", name="Get all bills")
async def get_all_bills(
    _: UserDataSchema = Depends(required_service(["1"])),
):
    return await zoho_get_all("/books/v3/bills", include_org=True)


@router.post("/bill", name="Create Bill")
async def create_bill(
    bill,
    _: UserDataSchema = Depends(required_service(["1"])),
):
    return await zoho_post(
        "/books/v3/bills", data=bill.model_dump(mode="json"), include_org=True
    )


@router.get("/taxes")
async def get_all_taxes(
    _: UserDataSchema = Depends(required_service(["1"])),
):
    return await zoho_get_all("/books/v3/settings/taxes", include_org=True)


@router.post("/vendor")
async def create_vendor(
    vendor,
    _: UserDataSchema = Depends(required_service(["1"])),
):
    return await zoho_post(
        "/books/v3/contacts", data=vendor.model_dump(mode="json"), include_org=True
    )


@router.get("/chartofaccounts")
async def get_all_chartofaccounts(
    _: UserDataSchema = Depends(required_service(["1"])),
):
    return await zoho_get_all("/books/v3/chartofaccounts", include_org=True)


@router.post("/bill/{bill_id}/attachment", name="Attach file to Bill")
async def attach_bill_file(
    bill_id: str,
    file: UploadFile = File(...),
    _: UserDataSchema = Depends(required_service(["1"])),
):
    return await zoho_post_file(
        f"/books/v3/bills/{bill_id}/attachment", file, include_org=True
    )
