import httpx
from typing import List

from app.core.exceptions.types import CustomAppException
from app.core.interface.provider_config import ProviderConfig
from app.services.openai.schemas.account_category import AccountCategory
from app.services.zoho.schemas.chart_of_accounts_response import ZohoAccountResponse
from app.core.settings import settings


class OpenAIService:
    def __init__(self, config: ProviderConfig):
        self.path = config.path

    async def classify_expense(
        self, text: str, accounts: List[ZohoAccountResponse]
    ) -> AccountCategory:
        url = f"{self.path}/classify-expense"
        chart = [account.clean_payload() for account in accounts]

        timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT_CONNECT,
            read=settings.HTTP_TIMEOUT_READ,
            write=settings.HTTP_TIMEOUT_WRITE,
            pool=settings.HTTP_TIMEOUT_POOL,
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    json={"text": text, "chart_of_accounts": chart},
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
