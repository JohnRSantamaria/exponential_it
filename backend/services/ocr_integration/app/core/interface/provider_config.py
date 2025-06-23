from pydantic import BaseModel


class ProviderConfig(BaseModel):
    server_url: str
    token: str | None = None
    user: str | None = None
    password: str | None = None
    api_prefix: str | None = None

    @property
    def path(self) -> str:
        if self.api_prefix:
            return f"{self.server_url.rstrip('/')}/{self.api_prefix.lstrip('/')}"
        return self.server_url
