import httpx
from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from exponential_core.exceptions.base import CustomAppException


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
        files = {
            "file": (file_name, file_content, content_type),
            "extractLineItems": (None, "true"),
            "extractTime": (None, "false"),
            "refresh": (None, "false"),
            "incognito": (None, "false"),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url=self.path,
                    headers={
                        "accept": "application/json",
                        "apikey": self.api_key,
                    },
                    files=files,
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                raise CustomAppException(
                    f"Error HTTP al comunicarse con Taggun ({e.response.status_code}): {e.response.text}"
                )

            except httpx.RequestError as e:
                raise CustomAppException(
                    f"Error de red al comunicarse con Taggun: {str(e)}"
                )

            except Exception as e:
                raise CustomAppException(f"Error inesperado en ocr_taggun: {str(e)}")
