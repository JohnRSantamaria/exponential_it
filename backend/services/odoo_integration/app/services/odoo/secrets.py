from exponential_core.secrets import SecretManager
from app.services.odoo.exceptions import OdooSecretsNotFound, MissingSecretKey


class SecretsService:
    def __init__(self, client_vat: str):
        self.client_vat = client_vat
        self.secret_name = f"exponentialit/{client_vat}"
        self.secret_manager = SecretManager(base_secret_name=self.secret_name)
        self._secrets = self.secret_manager.get_secret()

        if self._secrets is None or not self._secrets:
            raise OdooSecretsNotFound(client_vat=self.client_vat)

    def get_api_key(self) -> str:
        return self._get_required("api_key_odoo")

    def _get_required(self, key: str) -> str:
        value = self._secrets.get(key)
        if not value:
            raise MissingSecretKey(client_vat=self.client_vat, key=key)
        return value
