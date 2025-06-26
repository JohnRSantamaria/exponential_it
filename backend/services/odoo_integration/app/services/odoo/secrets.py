from exponential_core.secrets import SecretManager
from exponential_core.exceptions import (
    SecretsNotFound,
    MissingSecretKey,
    SecretsServiceNotLoaded,
)


class SecretsService:
    def __init__(self, company_vat: str):
        self.company_vat = company_vat
        self.secret_name = f"exponentialit/{company_vat}"
        self.secret_manager = SecretManager(base_secret_name=self.secret_name)
        self._secrets = None

    async def load(self):
        self._secrets = await self.secret_manager.get_secret()
        if not self._secrets:
            raise SecretsNotFound(company_vat=self.company_vat)
        return self

    def get_api_key(self) -> str:
        return self._get_required("API_KEY_ODOO")

    def get_url(self) -> str:
        return self._get_required("URL_ODOO")

    def get_db(self) -> str:
        return self._get_required("DB_ODOO")

    def get_username(self) -> str:
        return self._get_required("USERNAME_ODOO")

    def _get_required(self, key: str) -> str:
        if self._secrets is None:
            raise SecretsServiceNotLoaded()
        value = self._secrets.get(key)
        if not value:
            raise MissingSecretKey(company_vat=self.company_vat, key=key)
        return value
