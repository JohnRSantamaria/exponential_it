import json
import httpx
import urllib.parse

from typing import Optional
from fastapi import APIRouter, Query

from app.core.settings import settings
from app.services.zoho.schemas.tokens_response import ZohoTokenResponse
from app.services.zoho.secrets import SecretsServiceZoho
from app.core.logging import logger

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/", summary="Proceso completo de autorización Zoho")
async def full_zoho_auth_flow(
    company_vat: Optional[str] = Query(
        None, description="VAT o NIT de la empresa", example="B70845755"
    ),
    code: str = Query(
        None,
        description="Código de autorización (solo se pasa tras el consentimiento manual)",
        include_in_schema=False,
    ),
    state: str = Query("", description="Company vat", include_in_schema=False),
):
    if state:
        company_vat = state

    if not company_vat:
        return {"error": "Falta el parámetro company_vat."}

    secrets_service = await SecretsServiceZoho(company_vat=company_vat).load()
    base_url = settings.ZOHO_BASE_URL

    if not code:
        logger.debug("Generacion de URL de atorización para la obteción del código.")
        params = {
            "client_id": secrets_service.get_client_id(),
            "response_type": "code",
            "scope": "ZohoBooks.fullaccess.all",
            "redirect_uri": settings.ZOHO_REDIRECT_URI,
            "access_type": "offline",
            "prompt": "consent",
            "state": company_vat,
        }
        auth_url = f"{base_url}/oauth/v2/auth?" + urllib.parse.urlencode(params)
        return {"step": "authorization_required", "auth_url": auth_url}

    data = {
        "grant_type": "authorization_code",
        "client_id": secrets_service.get_client_id(),
        "client_secret": secrets_service.get_client_secret(),
        "redirect_uri": settings.ZOHO_REDIRECT_URI,
        "code": code,
    }

    logger.debug(
        f"Actulización o generación AWS secrets para la empresa : {company_vat}"
    )

    async with httpx.AsyncClient() as client:
        token_response = await client.post(f"{base_url}/oauth/v2/token", data=data)

    if token_response.status_code != 200:
        return {"error": "Failed to retrieve tokens", "details": token_response.text}

    tokens_raw = token_response.json()
    tokens = ZohoTokenResponse.from_response(tokens_raw)

    access_token = tokens.ACCESS_TOKEN
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    api_domain = tokens_raw.get("api_domain", settings.ZOHO_API_DOMAIN)

    organization_name = secrets_service.get_organization_name()
    logger.debug(f"Obtención del ID de la organizacion {organization_name}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{api_domain}/books/v3/organizations", headers=headers
            )
            response.raise_for_status()

            if not response.content:
                return {"error": "La respuesta de Zoho está vacía."}

            org_data = response.json()

    except httpx.HTTPStatusError as http_err:
        return {
            "error": f"Error HTTP al obtener organizaciones: {http_err.response.status_code}",
            "details": http_err.response.text,
        }
    except json.JSONDecodeError:
        return {
            "error": "La respuesta de Zoho no es un JSON válido.",
            "details": response.text,
        }
    except Exception as e:
        return {
            "error": "Error inesperado al consultar organizaciones.",
            "details": str(e),
        }

    organizations = org_data.get("organizations", [])
    if not organizations:
        return {"error": "No organizations found in Zoho response."}

    org_id = next(
        (
            org.get("organization_id")
            for org in organizations
            if org.get("name") == organization_name
        ),
        None,
    )

    if not org_id:
        return {"error": f"Organization '{organization_name}' not found."}

    # Combinar tokens + organization_id para guardar en AWS
    merged_data = tokens.model_dump(mode="json", exclude_none=True)
    merged_data["ORGANIZATION_ID"] = str(org_id)

    await secrets_service.update_tokens_aws(tokens=merged_data)

    return {
        "message": "Proceso completo exitoso.",
        "refresh_token": tokens.REFRESH_TOKEN,
        "expires_at": tokens.EXPIRES_AT,
        "organization_id": org_id,
        "organization_name": organization_name,
    }
