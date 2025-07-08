import json
import httpx

from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone

from app.core.settings import settings
from app.services.zoho.schemas.tokens_response import ZohoTokenResponse
from app.services.zoho.secrets import SecretsServiceZoho


async def get_access_token(secrets_service: SecretsServiceZoho) -> str:

    access_token = secrets_service.get_access_token()
    expires_at_str = secrets_service.get_expires_at()
    refresh_token = secrets_service.get_refresh_token()
    client_id = secrets_service.get_client_id()
    client_secret = secrets_service.get_client_secret()

    if access_token and expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now(timezone.utc) < (expires_at - timedelta(minutes=5)):
            return access_token

    if not refresh_token:
        raise HTTPException(
            status_code=403,
            detail="No refresh token available. Authenticate first. service: [Zoho_integraion]",
        )

    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            f"{settings.ZOHO_BASE_URL}/oauth/v2/token", data=data
        )

    tokens_raw = token_response.json()
    tokens = ZohoTokenResponse.from_response(tokens_raw)

    raw_data = tokens.model_dump(mode="json", exclude_none=True)
    await secrets_service.update_tokens_aws(tokens=raw_data)

    return raw_data.get("ACCESS_TOKEN")
