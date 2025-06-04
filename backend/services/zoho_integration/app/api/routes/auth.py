import httpx
import urllib.parse

from fastapi import APIRouter, Query, Request

from app.core.settings import settings
from app.services.zoho.client import zoho_get
from app.services.zoho.tokens import (
    load_organization_id,
    save_organization_id,
    save_tokens_with_expiry,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/", summary="llamar primero")
def oauth_start():
    params = {
        "client_id": settings.ZOHO_CLIENT_ID,
        "response_type": "code",
        "scope": "ZohoBooks.fullaccess.all",
        "redirect_uri": settings.ZOHO_REDIRECT_URI,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{settings.ZOHO_BASE_URL}/oauth/v2/auth?" + urllib.parse.urlencode(params)
    return {"auth_url": url}


@router.get("/callback", include_in_schema=False)
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "Athorization code not found."}

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.ZOHO_CLIENT_ID,
        "client_secret": settings.ZOHO_CLIENT_SECRET,
        "redirect_uri": settings.ZOHO_REDIRECT_URI,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ZOHO_BASE_URL}/oauth/v2/token", data=data
        )

    tokens = response.json()

    save_tokens_with_expiry(tokens)

    return {"message": "Tokens saved", "tokens": tokens}


@router.get("/organization", summary="llamar segundo")
async def get_organizations(
    organization_name: str = Query(
        default="Exponential IT", description="Organización a buscar"
    )
):
    response = await zoho_get("/books/v3/organizations")
    org_id = None

    organizations = response.get("organizations", [])
    if not organizations:
        return {"error": "No organizations found in Zoho response."}

    for organization in organizations:
        if organization.get("name", None) == organization_name:
            org_id = organization.get("organization_id", None)

    if not org_id:
        return {"error": f"Not found organization with name : {organization_name}"}

    organization_id = load_organization_id()
    organization_id["organization_id"] = org_id
    save_organization_id(organization_id)

    return {
        "message": "Organization ID stored successfully.",
        "organization_id": org_id,
        "organization_name": organization_name,
    }
