from app.services.admin.client import AdminService
from app.core.client_provider import ProviderConfig
from app.core.settings import settings


async def register_scan(user_id: int, account_id: int):
    adm_service = AdminService(config=ProviderConfig(server_url=settings.URL_ADMIN))
    return await adm_service.register_scan(user_id=user_id, account_id=account_id)
