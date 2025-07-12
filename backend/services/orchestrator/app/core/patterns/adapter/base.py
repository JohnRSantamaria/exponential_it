from app.core.patterns.adapter.odoo_adapter import OdooAdapter
from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from app.core.patterns.adapter.zoho_adapter import ZohoAdapter
from app.core.schemas.enums import ServicesEnum


def get_provider(
    service: ServicesEnum,
    company_vat: str,
    version: str | None = None,
) -> ZohoAdapter | OdooAdapter:
    if service == ServicesEnum.ZOHO:
        config = ProviderConfig(
            server_url=settings.URL_ZOHO,
            api_prefix="/books",
            company_vat=company_vat,
        )
        return ZohoAdapter(config=config)
    elif service == ServicesEnum.ODOO:
        if version == "v16":
            config = ProviderConfig(
                server_url=settings.URL_ODOO,
                api_prefix="/odoo/v16",
                company_vat=company_vat,
            )
        elif version == "v18":
            config = ProviderConfig(
                server_url=settings.URL_ODOO,
                api_prefix="/odoo/v18",
                company_vat=company_vat,
            )
        else:
            raise NotImplementedError(
                f"La versión {version} aún no ha sido implementada"
            )

        return OdooAdapter(config=config)
    else:
        raise NotImplementedError(f"{service} :aún no ha sido implementado.")
