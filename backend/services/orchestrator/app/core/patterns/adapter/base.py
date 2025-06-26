from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from app.core.patterns.adapter.zoho_adapter import ZohoAdapter
from app.core.schemas.enums import ServicesEnum


def get_provider(service: ServicesEnum):
    if service == ServicesEnum.ZOHO:
        config = ProviderConfig(server_url=settings.URL_ZOHO, api_prefix="/api/books")
        return ZohoAdapter(config=config)
    elif service == ServicesEnum.ODOO:
        return
    else:
        raise NotImplementedError(f"{service} : No ha sido implementado aun.")
