from app.services.admin.client import AdminService
from app.services.taggun.exceptions import AccountNotFoundError, AdminServiceError
from app.core.client_provider import ProviderConfig
from app.core.settings import settings
from exponential_core.exceptions import CustomAppException


async def get_accounts_by_email(email: str):
    adm_service = AdminService(config=ProviderConfig(server_url=settings.URL_ADMIN))
    try:
        response = await adm_service.identify_accounts(email=email)
    except CustomAppException as e:
        raise AdminServiceError(message=str(e))

    if not response.accounts:
        raise AccountNotFoundError(data={"email": email})

    return response
