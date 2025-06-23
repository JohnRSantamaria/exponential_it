"""Patron de diseño adapter"""

from app.core.interface.account_provider import AccountingProvider
from app.core.interface.crete_provider import CreateProvider
from app.core.interface.provider_config import ProviderConfig


class OdooAdapter(AccountingProvider, CreateProvider):
    def __init__(self, config: ProviderConfig):
        self.url = config.path

    async def register_company(self, client_vat: str):
        pass
