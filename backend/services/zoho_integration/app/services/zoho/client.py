import httpx

from fastapi import HTTPException, UploadFile
from urllib.parse import urlencode, urljoin, urlparse, parse_qsl, urlunparse

from app.core.settings import settings
from app.services.zoho.tokens import get_access_token, load_organization_id


async def zoho_get(path: str, include_org: bool = False):
    token = await get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    organization_id = load_organization_id()
    org_id = organization_id.get("organization_id")

    if include_org and not org_id:
        raise HTTPException(
            status_code=400, detail=f"Organization id no ha sido definido."
        )

    url_parts = list(urlparse(path))
    query = dict(parse_qsl(url_parts[4]))

    if include_org and org_id and "organization_id" not in query:
        query["organization_id"] = org_id

    url_parts[4] = urlencode(query)
    final_path = urlunparse(url_parts)

    url = urljoin(settings.ZOHO_API_DOMAIN, final_path)

    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
    return response.json()


async def zoho_post(path: str, data: dict, include_org: bool = False):
    token = await get_access_token()
    organization_id = load_organization_id()
    org_id = organization_id.get("organization_id")
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }

    if include_org:
        if org_id and "organization_id=" not in path:
            path += ("&" if "?" in path else "?") + f"organization_id={org_id}"

    url = f"{settings.ZOHO_API_DOMAIN}{path}"

    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, json=data)

    return response.json()


async def zoho_post_file(path: str, file: UploadFile, include_org: bool = False):
    token = await get_access_token()
    organization_id = load_organization_id()
    org_id = organization_id.get("organization_id")

    url_parts = list(urlparse(path))
    query = dict(parse_qsl(url_parts[4]))

    if include_org and org_id and "organization_id" not in query:
        query["organization_id"] = org_id

    url_parts[4] = urlencode(query)
    final_path = urlunparse(url_parts)
    url = urljoin(settings.ZOHO_API_DOMAIN, final_path)

    file_content = await file.read()
    files = {"attachment": (file.filename, file_content, file.content_type)}
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}

    timeout = httpx.Timeout(120.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url=url, headers=headers, files=files)

    return response.json()


async def zoho_get_all(
    path: str, include_org: bool = False, page_param: str = "page", per_page: int = 200
):
    all_data = []
    page = 1

    while True:
        paginated_path = f"{path}?{page_param}={page}&per_page={per_page}"

        data = await zoho_get(paginated_path, include_org=include_org)

        # Get data key
        data_key = next((k for k in data if isinstance(data[k], list)), None)
        if not data_key:
            break

        batch = data[data_key]
        all_data.extend(batch)

        if not data.get("page_context", {}).get("has_more_page", False):
            break

        page += 1

    return all_data
