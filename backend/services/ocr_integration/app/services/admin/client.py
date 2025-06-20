import httpx
from app.core.settings import settings
from app.core.interface.provider_config import ProviderConfig
from app.services.admin.schemas import ServiceCredentialsResponse

from exponential_core.exceptions import CustomAppException


class AdminService:
    def __init__(self, config: ProviderConfig):
        self.path = config.path
        self.token = config.token

    async def register_scan(self, user_id):
        url = f"{self.path}/auth/users/{user_id}/register-scan/"

        timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT_CONNECT,
            read=settings.HTTP_TIMEOUT_READ,
            write=settings.HTTP_TIMEOUT_WRITE,
            pool=settings.HTTP_TIMEOUT_POOL,
        )

        headers = {"Authorization": self.token}

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url=url,
                    headers=headers,
                )
                response.raise_for_status()

                return response.json()

        except httpx.ReadTimeout:
            raise CustomAppException(
                "Tiempo de espera excedido al clasificar con Admin"
            )

        except httpx.RequestError as exc:
            raise CustomAppException(f"Error de conexión con Admin: {exc}")

        except Exception as exc:
            raise CustomAppException(f"Error inesperado al clasificar con Admin: {exc}")

    async def service_credentials(
        self, service_id: int, search=None
    ) -> ServiceCredentialsResponse:
        url = f"{self.path}/services/{service_id}/credentials/"

        if search:
            url += f"?search={search}"

        timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT_CONNECT,
            read=settings.HTTP_TIMEOUT_READ,
            write=settings.HTTP_TIMEOUT_WRITE,
            pool=settings.HTTP_TIMEOUT_POOL,
        )

        headers = {"Authorization": self.token}

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    url=url,
                    headers=headers,
                )
                response.raise_for_status()

                data = response.json()

                return ServiceCredentialsResponse(**data)

        except httpx.ReadTimeout:
            raise CustomAppException(
                "Tiempo de espera excedido al clasificar con Admin"
            )

        except httpx.RequestError as exc:
            raise CustomAppException(f"Error de conexión con Admin: {exc}")

        except Exception as exc:
            raise CustomAppException(f"Error inesperado al clasificar con Admin: {exc}")
