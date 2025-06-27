from app.core.patterns.adapter.odoo_adapter import OdooAdapter
from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from app.core.patterns.adapter.zoho_adapter import ZohoAdapter
from app.core.schemas.enums import ServicesEnum


def get_provider(
    service: ServicesEnum,
    company_vat: str | None = None,
) -> ZohoAdapter | OdooAdapter:
    if service == ServicesEnum.ZOHO:
        config = ProviderConfig(server_url=settings.URL_ZOHO, api_prefix="/api/books")
        return ZohoAdapter(config=config)
    elif service == ServicesEnum.ODOO:
        config = ProviderConfig(
            server_url=settings.URL_ODOO,
            api_prefix="/odoo",
            company_vat=company_vat,
        )
        return OdooAdapter(config=config)
    else:
        raise NotImplementedError(f"{service} : No ha sido implementado aun.")
