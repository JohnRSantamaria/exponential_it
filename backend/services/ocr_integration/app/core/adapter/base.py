from app.core.settings import settings
from app.core.enums import ServicesEnum
from app.services.odoo.adapter import OdooAdapter
from app.services.zoho.adapter import ZohoAdapter
from app.core.interface.provider_config import ProviderConfig
from app.core.interface.account_provider import AccountingProvider


def get_provider(service: ServicesEnum) -> AccountingProvider:
    if service == ServicesEnum.ZOHO:
        return ZohoAdapter(
            config=ProviderConfig(
                server_url=settings.URL_ZOHO,
                api_prefix="/api/v1/zoho/books",
            )
        )
    if service == ServicesEnum.ODOO:
        return OdooAdapter(config=ProviderConfig(server_url=""))
    else:
        raise NotImplementedError("No está implementado para este proveedor")
