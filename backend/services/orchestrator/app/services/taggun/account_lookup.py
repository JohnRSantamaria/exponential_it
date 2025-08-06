from app.services.admin.client import AdminService
from app.services.taggun.exceptions import AccountNotFoundError, AdminServiceError
from app.core.client_provider import ProviderConfig
from app.core.settings import settings
from exponential_core.exceptions import CustomAppException
from app.core.logging import logger


async def get_accounts_by_email(email: str):
    adm_service = AdminService(config=ProviderConfig(server_url=settings.URL_ADMIN))
    try:
        logger.debug(f"Buscando el email : {email}")
        response = await adm_service.identify_accounts(email=email)
        logger.debug(response.model_dump(mode="json", exclude_none=True))

    except CustomAppException as e:
        raise AdminServiceError(message=str(e))

    if not response.accounts:
        raise AccountNotFoundError(data={"email": email})

    return response
