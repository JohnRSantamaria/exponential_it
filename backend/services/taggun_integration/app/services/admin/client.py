import httpx
from app.core.settings import settings

from ...core.client_provider import ProviderConfig
from .schemas import IdentifyAccountsResponse, ServiceCredentialsResponse
from exponential_core.exceptions import CustomAppException


class AdminService:
    def __init__(self, config: ProviderConfig):
        self.path = config.path
        self.timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT_CONNECT,
            read=settings.HTTP_TIMEOUT_READ,
            write=settings.HTTP_TIMEOUT_WRITE,
            pool=settings.HTTP_TIMEOUT_POOL,
        )

    async def register_scan(self, user_id: int, account_id: int) -> dict:
        url = f"{self.path}/auth/users/register-scan/"

        data = {"user_id": user_id, "account_id": account_id}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=url,
                    data=data,
                )
                response.raise_for_status()
            return response.json()
        except httpx.ReadTimeout:
            raise CustomAppException(
                "Tiempo de espera excedido al registrar escaneo en Admin"
            )
        except httpx.RequestError as exc:
            raise CustomAppException(f"Error de conexión con Admin: {exc}")
        except Exception as exc:
            raise CustomAppException(
                f"Error inesperado al registrar escaneo con Admin: {exc}"
            )

    async def service_credentials(
        self, service_id: int, search: str | None = None
    ) -> ServiceCredentialsResponse:
        url = f"{self.path}/services/{service_id}/credentials/"
        if search:
            url += f"?search={search}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url=url, headers=self.headers)
                response.raise_for_status()
            return ServiceCredentialsResponse(**response.json())
        except httpx.ReadTimeout:
            raise CustomAppException(
                "Tiempo de espera excedido al obtener credenciales de servicio"
            )
        except httpx.RequestError as exc:
            raise CustomAppException(f"Error de conexión con Admin: {exc}")
        except Exception as exc:
            raise CustomAppException(
                f"Error inesperado al obtener credenciales con Admin: {exc}"
            )

    async def identify_accounts(self, email: str) -> IdentifyAccountsResponse:
        url = f"{self.path}/auth/users/identify/"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url=url, json={"email": email})
                response.raise_for_status()

            return IdentifyAccountsResponse(**response.json())

        except httpx.ReadTimeout:
            raise CustomAppException(
                "Tiempo de espera excedido al obtener credenciales de servicio"
            )
        except httpx.RequestError as exc:
            raise CustomAppException(f"Error de conexión con Admin: {exc}")
        except Exception as exc:
            raise CustomAppException(
                f"Error inesperado al obtener credenciales con Admin: {exc}"
            )
