"""Patron de diseño adapter"""

from app.core.interface.account_provider import AccountingProvider
from app.core.interface.provider_config import ProviderConfig


class OdooAdapter(AccountingProvider):
    def __init__(self, config: ProviderConfig):
        self.user = config.user
        self.password = config.password
    