import json
import httpx

from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

from app.core.settings import settings


async def get_access_token():

    tokens = load_tokens()

    access_token = tokens.get("access_token", None)
    expires_at_str = tokens.get("expires_at", None)
    if access_token and expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now(timezone.utc) < (expires_at - timedelta(minutes=5)):
            return access_token

    if "refresh_token" not in tokens:
        raise HTTPException(
            status_code=403,
            detail="No refresh token available. Authenticate first. service: [Zoho_integraion]",
        )

    data = {
        "grant_type": "refresh_token",
        "client_id": settings.ZOHO_CLIENT_ID,
        "client_secret": settings.ZOHO_CLIENT_SECRET,
        "refresh_token": tokens["refresh_token"],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ZOHO_BASE_URL}/oauth/v2/token", data=data
        )

    new_tokens = response.json()

    if "access_token" not in new_tokens:
        raise HTTPException(
            status_code=403, detail=f"Token refresh failed: {new_tokens}"
        )

    new_tokens["refresh_token"] = tokens["refresh_token"]

    save_tokens_with_expiry(new_tokens)

    return new_tokens["access_token"]


def save_tokens_with_expiry(tokens: dict):
    expires_in = tokens.get("expires_in")
    settings.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    if expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        tokens["expires_at"] = expires_at.isoformat()
    save_tokens(tokens)


def save_tokens(data: dict):
    settings.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with settings.TOKEN_FILE.open("w") as f:
        json.dump(data, f)


def save_organization_id(data: dict):
    with settings.ORGANIZATION_FILE.open("w") as f:
        json.dump(data, f)


def load_tokens() -> dict:
    if not settings.TOKEN_FILE.exists() or settings.TOKEN_FILE.stat().st_size == 0:
        return {}
    with settings.TOKEN_FILE.open("r") as f:
        return json.load(f)


def load_organization_id() -> dict:
    if (
        not settings.ORGANIZATION_FILE.exists()
        or settings.ORGANIZATION_FILE.stat().st_size == 0
    ):
        return {}
    with settings.ORGANIZATION_FILE.open("r") as f:
        return json.load(f)
