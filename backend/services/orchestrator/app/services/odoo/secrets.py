from exponential_core.secrets import SecretManager
from exponential_core.exceptions import SecretsNotFound, MissingSecretKey


class SecretsServiceOdoo:
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

    def get_tax_id(self) -> int:
        if self._secrets is None:
            return ""
        return self._secrets.get("TAX_ID_ODOO") or ""

    def _get_required(self, key: str) -> str:
        if self._secrets is None:
            raise RuntimeError(
                "SecretsService.load() no fue llamado antes de acceder a los secretos."
            )
        value = self._secrets.get(key)
        if not value:
            raise MissingSecretKey(company_vat=self.company_vat, key=key)
        return value
