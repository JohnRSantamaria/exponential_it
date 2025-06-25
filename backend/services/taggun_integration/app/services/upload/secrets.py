from exponential_core.secrets import SecretManager
from exponential_core.exceptions import SecretsNotFound, MissingSecretKey


class SecretsService:
    def __init__(self, company_vat: str):
        self.company_vat = company_vat
        self.secret_name = f"exponentialit/{company_vat}"
        self.secret_manager = SecretManager(base_secret_name=self.secret_name)
        self._secrets = self.secret_manager.get_secret()

        if self._secrets is None or not self._secrets:
            raise SecretsNotFound(company_vat=self.company_vat)

    def get_dropbox_access_token(self) -> str:
        return self._get_required("DROPBOX_ACCESS_TOKEN")

    def get_dropbox_refresh_token(self) -> str:
        return self._get_required("DROPBOX_REFRESH_TOKEN")

    def get_dropbox_app_key(self) -> str:
        return self._get_required("DROPBOX_APP_KEY")

    def get_dropbox_app_secret(self) -> str:
        return self._get_required("DROPBOX_APP_SECRET")

    def get_dropbox_credentials(self) -> dict:
        return {
            "access_token": self.get_dropbox_access_token(),
            "refresh_token": self.get_dropbox_refresh_token(),
            "app_key": self.get_dropbox_app_key(),
            "app_secret": self.get_dropbox_app_secret(),
        }

    def _get_required(self, key: str) -> str:
        value = self._secrets.get(key)
        if not value:
            raise MissingSecretKey(company_vat=self.company_vat, key=key)
        return value
