import httpx
import urllib.parse

from fastapi import APIRouter, Query, Request

from app.services.zoho.client import zoho_get
from app.services.zoho.secrets import SecretsServiceZoho
from app.services.zoho.tokens import (
    load_organization_id,
    save_organization_id,
    save_tokens_with_expiry,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/", summary="llamar primero")
async def oauth_start(
    company_vat: str = Query(
        default="B70845755",
        description="VAT o NIT de la empresa para obtener los secretos de Zoho",
    )
):

    if not company_vat:
        return {"error": "company_vat not found."}

    secrets_service = await SecretsServiceZoho(company_vat=company_vat).load()

    params = {
        "client_id": secrets_service.get_client_id(),
        "response_type": "code",
        "scope": "ZohoBooks.fullaccess.all",
        "redirect_uri": secrets_service.get_redirect_uri(),
        "access_type": "offline",
        "prompt": "consent",
    }

    base_url = secrets_service.get_base_url()
    url = f"{base_url}/oauth/v2/auth?" + urllib.parse.urlencode(params)
    return {"auth_url": url}


@router.get("/callback", include_in_schema=False)
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    company_vat = request.query_params.get("company_vat")

    secrets_service = await SecretsServiceZoho(company_vat=company_vat).load()

    if not code:
        return {"error": "Athorization code not found."}
    if not company_vat:
        return {"error": "company_vat not found."}

    data = {
        "grant_type": "authorization_code",
        "client_id": secrets_service.get_client_id(),
        "client_secret": secrets_service.get_client_secret(),
        "redirect_uri": secrets_service.get_redirect_uri(),
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        base_url = secrets_service.get_base_url()
        response = await client.post(
            f"{base_url}/oauth/v2/token",
            data=data,
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
