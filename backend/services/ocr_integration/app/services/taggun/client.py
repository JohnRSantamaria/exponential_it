import httpx
import base64

from app.core.settings import settings


async def send_file_to_taggun(
    file_name: str, file_content: bytes, content_type: str, api_key: str
) -> dict:
    headers = {
        "apikey": api_key,
    }
    files = {
        "file": (file_name, file_content, content_type),
    }

    timeout = httpx.Timeout(
        connect=settings.HTTP_TIMEOUT_CONNECT,
        read=settings.HTTP_TIMEOUT_READ,
        write=settings.HTTP_TIMEOUT_WRITE,
        pool=settings.HTTP_TIMEOUT_POOL,
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url=settings.TAGGUN_URL,
            headers=headers,
            files=files,
        )
        response.raise_for_status()
        return response.json()
