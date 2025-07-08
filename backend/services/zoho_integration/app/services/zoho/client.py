import httpx
from fastapi import HTTPException, UploadFile, status
from urllib.parse import urlencode, urljoin, urlparse, parse_qsl, urlunparse

from app.core.settings import settings
from app.services.zoho.secrets import SecretsServiceZoho
from app.services.zoho.tokens import get_access_token


async def _get_secrets_and_token(company_vat: str) -> tuple[SecretsServiceZoho, str]:
    """Función base para validar parámetros"""
    if not company_vat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'company_vat' es obligatorio.",
        )

    secrets_service = await SecretsServiceZoho(company_vat=company_vat).load()
    token = await get_access_token(secrets_service=secrets_service)
    return secrets_service, token


def _build_url(path: str, include_org: bool, organization_id: str = "") -> str:
    """Función base para construir URL final"""
    url_parts = list(urlparse(path))
    query = dict(parse_qsl(url_parts[4]))

    if include_org and organization_id and "organization_id" not in query:
        query["organization_id"] = organization_id

    url_parts[4] = urlencode(query)
    return urljoin(settings.ZOHO_API_DOMAIN, urlunparse(url_parts))


async def zoho_get(path: str, company_vat: str = "", include_org: bool = False):
    secrets_service, token = await _get_secrets_and_token(company_vat)
    organization_id = secrets_service.get_organization_id()

    if include_org and not organization_id:
        raise HTTPException(status_code=400, detail="Organization ID no definido.")

    url = _build_url(path, include_org, organization_id)
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    return response.json()


async def zoho_post(
    path: str, data: dict, company_vat: str = "", include_org: bool = False
):
    secrets_service, token = await _get_secrets_and_token(company_vat)
    organization_id = secrets_service.get_organization_id()

    if include_org and not organization_id:
        raise HTTPException(status_code=400, detail="Organization ID no definido.")

    url = _build_url(path, include_org, organization_id)
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
    return response.json()


async def zoho_post_file(
    path: str,
    file: UploadFile,
    company_vat: str = "",
    include_org: bool = False,
):
    secrets_service, token = await _get_secrets_and_token(company_vat)
    organization_id = secrets_service.get_organization_id()

    if include_org and not organization_id:
        raise HTTPException(status_code=400, detail="Organization ID no definido.")

    url = _build_url(path, include_org, organization_id)
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}

    file_content = await file.read()
    files = {"attachment": (file.filename, file_content, file.content_type)}
    timeout = httpx.Timeout(120.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, files=files)
    return response.json()


async def zoho_get_all(
    path: str,
    company_vat: str = "",
    include_org: bool = False,
    page_param: str = "page",
    per_page: int = 200,
):
    if not company_vat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'company_vat' es obligatorio.",
        )

    all_data = []
    page = 1

    while True:
        paginated_path = f"{path}?{page_param}={page}&per_page={per_page}"
        data = await zoho_get(paginated_path, company_vat, include_org)

        data_key = next((k for k in data if isinstance(data[k], list)), None)
        if not data_key:
            break

        batch = data[data_key]
        all_data.extend(batch)

        if not data.get("page_context", {}).get("has_more_page", False):
            break

        page += 1

    return all_data
