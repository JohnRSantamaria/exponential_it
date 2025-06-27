from pydantic import BaseModel


class ProviderConfig(BaseModel):
    server_url: str
    api_prefix: str | None = None
    api_key: str | None = None
    company_vat: str | None = None

    @property
    def path(self) -> str:
        if self.api_prefix:
            return f"{self.server_url.rstrip('/')}/{self.api_prefix.lstrip('/')}"
        return self.server_url
