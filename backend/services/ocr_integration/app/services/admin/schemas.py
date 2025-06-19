from pydantic import BaseModel
from typing import List

from app.core.crypto import decrypt_value


class UserDataSchema(BaseModel):
    user_id: int
    email: str
    active_subscriptions: List[int]
    exp: int
    account_id: int
    account_name: str

    class Config:
        from_attributes = True  # Pydantic v2 — reemplaza orm_mode


class CredentialOut(BaseModel):
    key: str
    value: str  # Siempre string para ser JSON-safe

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_safe(cls, cred) -> "CredentialOut":
        raw_value = cred.value
        if isinstance(raw_value, memoryview):
            raw_value = raw_value.tobytes()

        if cred.is_secret:
            decrypted = decrypt_value(raw_value)
            value = (
                decrypted.decode() if isinstance(decrypted, bytes) else str(decrypted)
            )
        else:
            value = (
                raw_value.decode() if isinstance(raw_value, bytes) else str(raw_value)
            )

        key = str(cred.key).lower().strip()

        return cls(key=key, value=value)


class Credential(BaseModel):
    id: int
    key: str
    value: str
    is_secret: bool


class ServiceCredentialsResponse(BaseModel):
    service: str
    service_name: str
    credentials: List[Credential]


class ExtractedCredentials(BaseModel):
    cif: str
    processor: str
    storage: str
    taggun: str
