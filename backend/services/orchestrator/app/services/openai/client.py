import httpx
from typing import List

from app.core.client_provider import ProviderConfig
from app.services.openai.schemas.account_category import AccountCategory
from app.core.settings import settings

from exponential_core.exceptions import CustomAppException
from app.core.logging import logger


class OpenAIService:
    def __init__(self, config: ProviderConfig):
        self.path = config.path
        self.timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT_CONNECT,
            read=settings.HTTP_TIMEOUT_READ,
            write=settings.HTTP_TIMEOUT_WRITE,
            pool=settings.HTTP_TIMEOUT_POOL,
        )

    async def classify_expense(self, text: str, accounts: str) -> AccountCategory:
        url = f"{self.path}/classify-expense"
        logger.debug(f"Clasificando en OpenAI: {url}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={"text": text, "chart_of_accounts": accounts},
                )
            response.raise_for_status()
            return AccountCategory(**response.json())

        except httpx.ReadTimeout:
            raise CustomAppException(
                "Tiempo de espera excedido al clasificar con OpenAI"
            )

        except httpx.RequestError as exc:
            raise CustomAppException(f"Error de conexión con OpenAI: {exc}")

        except Exception as exc:
            raise CustomAppException(
                f"Error inesperado al clasificar con OpenAI: {exc}"
            )
