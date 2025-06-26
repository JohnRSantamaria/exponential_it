from pydantic import BaseModel


class ChartOfAccountsResponse(BaseModel):
    account_id: str
    account_name: str
    description: str
    account_type: str
    is_active: bool
