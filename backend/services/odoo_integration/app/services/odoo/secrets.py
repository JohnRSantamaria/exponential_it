from exponential_core.secrets import SecretManager
from exponential_core.exceptions import SecretsNotFound, MissingSecretKey


class SecretsService:
    def __init__(self, client_vat: str):
        self.client_vat = client_vat
        self.secret_name = f"exponentialit/{client_vat}"
        self.secret_manager = SecretManager(base_secret_name=self.secret_name)
        self._secrets = self.secret_manager.get_secret()

        if self._secrets is None or not self._secrets:
            raise SecretsNotFound(client_vat=self.client_vat)

    def get_api_key(self) -> str:
        return self._get_required("API_KEY_ODOO")

    def get_url(self) -> str:
        return self._get_required("URL_ODOO")

    def get_db(self) -> str:
        return self._get_required("DB_ODOO")

    def get_username(self) -> str:
        return self._get_required("USERNAME_ODOO")

    def _get_required(self, key: str) -> str:
        value = self._secrets.get(key)
        if not value:
            raise MissingSecretKey(client_vat=self.client_vat, key=key)
        return value
