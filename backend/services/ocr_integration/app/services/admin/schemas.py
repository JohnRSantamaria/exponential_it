from pydantic import BaseModel
from typing import List, Dict, Union

from app.core.crypto import decrypt_value


class UserDataSchema(BaseModel):
    user_id: int
    email: str
    active_subscriptions: List[Dict[int, str]]
    exp: int

    class Config:
        from_attributes = True  # Reemplaza orm_mode en Pydantic


class CredentialOut(BaseModel):
    key: str
    value: str  # siempre entregamos string para JSON

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_safe(cls, cred) -> "CredentialOut":
        raw_value = cred.value
        is_secret = cred.is_secret

        if is_secret:
            value = decrypt_value(raw_value)
        else:
            value = raw_value

        key = str(cred.key).lower().strip()

        return cls(key=key, value=value)
