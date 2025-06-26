from pydantic import BaseModel
from typing import List


class UserDataSchema(BaseModel):
    user_id: int
    email: str
    active_subscriptions: List[int]
    exp: int

    class Config:
        from_attributes = True


class CredentialItem(BaseModel):
    key: str
    value: str
    is_secret: bool


class ServiceCredentialsResponse(BaseModel):
    service: str
    service_name: str
    credentials: List[dict]


class AccountItem(BaseModel):
    account_id: int
    account_name: str
    account_tax_id: str


class IdentifyAccountsResponse(BaseModel):
    user_id: int
    accounts: List[AccountItem]
