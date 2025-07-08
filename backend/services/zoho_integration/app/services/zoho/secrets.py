from typing import Dict
from exponential_core.secrets import SecretManager
from exponential_core.exceptions import SecretsNotFound, MissingSecretKey


class SecretsServiceZoho:
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

    def get_client_id(self) -> str:
        return self._get_required("ZOHO_CLIENT_ID")

    def get_client_secret(self) -> str:
        return self._get_required("ZOHO_CLIENT_SECRET")

    def get_organization_name(self) -> str:
        return self._get_required("ORGANIZATION_NAME")

    def get_access_token(self) -> str:
        return self._get_required("ACCESS_TOKEN")

    def get_refresh_token(self) -> str:
        return self._get_required("REFRESH_TOKEN")

    def get_expires_at(self) -> str:
        return self._get_required("EXPIRES_AT")

    def get_organization_id(self) -> str:
        return self._get_required("ORGANIZATION_ID")

    def _get_required(self, key: str) -> str:
        if self._secrets is None:
            raise RuntimeError(
                "SecretsService.load() no fue llamado antes de acceder a los secretos."
            )
        value = self._secrets.get(key)
        if not value:
            raise MissingSecretKey(company_vat=self.company_vat, key=key)
        return value

    async def create_tokens_aws(self, tokens: Dict[str, str]):
        """
        Crea un nuevo secreto desde cero,
        #! Sobrescribe si ya existía.
        """
        if not isinstance(tokens, dict):
            raise ValueError("Los tokens deben ser un diccionario válido.")

        await self.secret_manager.create_secret(initial_data=tokens)
        self._secrets = tokens

    async def update_tokens_aws(self, tokens: Dict[str, str]):
        """Actualiza (o agrega) claves dentro del secreto existente."""
        if not isinstance(tokens, dict):
            raise ValueError("Los tokens deben ser un diccionario válido.")

        for key, value in tokens.items():
            await self.secret_manager.set_secret(key, value)

        self._secrets = await self.secret_manager.get_secret()
