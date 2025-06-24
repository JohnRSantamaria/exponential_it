import httpx
from app.core.settings import settings
from app.core.client_provider import ProviderConfig


class TaggunService:
    def __init__(self, config: ProviderConfig):
        self.path = config.path
        self.api_key = config.api_key
        self.timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT_CONNECT,
            read=settings.HTTP_TIMEOUT_READ,
            write=settings.HTTP_TIMEOUT_WRITE,
            pool=settings.HTTP_TIMEOUT_POOL,
        )

    async def ocr_taggun(
        self,
        file_name: str,
        file_content: bytes,
        content_type: str,
    ):
        headers = {
            "apikey": self.api_key,
        }

        files = {
            "file": (file_name, file_content, content_type),
        }

        data = {
            "extractLineItems": "true",
            "extractTime": "false",
            "refresh": "false",
            "incognito": "false",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url=self.path,
                headers=headers,
                data=data,
                files=files,
            )
            response.raise_for_status()
            return response.json()
