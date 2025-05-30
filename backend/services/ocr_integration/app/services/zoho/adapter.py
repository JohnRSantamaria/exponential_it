from abc import abstractmethod
from app.core.interface.account_provider import AccountingProvider
from app.core.interface.provider_config import ProviderConfig


class ZohoAdapter(AccountingProvider):
    def __init__(self, config: ProviderConfig):
        self.server_url = config.server_url

    async def get_all_contacts(self):
        return self.server_url
