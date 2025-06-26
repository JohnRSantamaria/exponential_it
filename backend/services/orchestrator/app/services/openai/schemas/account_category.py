from pydantic import BaseModel


class AccountCategory(BaseModel):
    account_id: str
    account_name: str
