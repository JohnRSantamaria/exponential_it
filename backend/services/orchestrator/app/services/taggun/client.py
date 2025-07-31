import httpx
import asyncio
import random
from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from exponential_core.exceptions.base import CustomAppException
from app.core.logging import logger


class TaggunService:
    """
    Cliente persistente para interactuar con Taggun.
    - Controla concurrencia con Semaphore.
    - Aplica throttle entre requests para evitar saturar la API.
    - Implementa reintentos con backoff exponencial en caso de 429.
    """

    def __init__(
        self,
        config: ProviderConfig,
        max_concurrent_requests: int = 5,
        min_delay: float = 0.3,
    ):
        self.path = config.path
        self.api_key = config.api_key
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.min_delay = min_delay  # tiempo mínimo entre requests
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=settings.HTTP_TIMEOUT_CONNECT,
                read=settings.HTTP_TIMEOUT_READ,
                write=settings.HTTP_TIMEOUT_WRITE,
                pool=settings.HTTP_TIMEOUT_POOL,
            )
        )
        self._last_request = 0.0

    async def close(self):
        """Cierra el cliente HTTP cuando se apaga la aplicación."""
        await self.client.aclose()

    async def _throttle(self):
        """Evita enviar requests demasiado rápido (respeta min_delay)."""
        now = asyncio.get_event_loop().time()
        wait = self.min_delay - (now - self._last_request)
        if wait > 0:
            logger.debug(f"[TAGGUN] Aplicando throttle, esperando {wait:.2f}s")
            await asyncio.sleep(wait)
        self._last_request = asyncio.get_event_loop().time()

    async def _send_request(
        self, file_name: str, file_content: bytes, content_type: str
    ):
        """Función que envía realmente la petición a Taggun."""
        files = {
            "file": (file_name, file_content[:], content_type),
            "extractLineItems": (None, "true"),
            "extractTime": (None, "false"),
            "refresh": (None, "false"),
            "incognito": (None, "false"),
        }

        response = await self.client.post(
            url=self.path,
            headers={
                "accept": "application/json",
                "apikey": self.api_key,
            },
            files=files,
        )
        response.raise_for_status()
        return response.json()

    async def _retry_with_backoff(self, func, *args, retries=3, base_delay=1.0):
        """Reintenta con backoff exponencial si hay error 429."""
        for attempt in range(retries):
            try:
                return await func(*args)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < retries - 1:
                    delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
                    logger.warning(
                        f"[TAGGUN] 429 Rate Limit - Reintentando en {delay:.2f}s (intento {attempt+1}/{retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise CustomAppException(
                        f"Error HTTP al comunicarse con Taggun ({e.response.status_code}): {e.response.text}"
                    )
            except Exception as e:
                raise CustomAppException(f"Error inesperado en ocr_taggun: {str(e)}")

    async def ocr_taggun(self, file_name: str, file_content: bytes, content_type: str):
        """Envía un archivo a Taggun aplicando control de concurrencia, throttle y reintentos."""
        async with self.semaphore:
            await self._throttle()  # ✅ asegura espaciar requests
            return await self._retry_with_backoff(
                self._send_request, file_name, file_content, content_type
            )
