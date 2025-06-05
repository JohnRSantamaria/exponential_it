from pydantic import BaseModel, ConfigDict
from typing import Dict, Optional, List
import datetime

from app.core.utils.base_models import BaseSanitizedModel


class CustomField(BaseModel):
    customfield_id: str
    value: str


class ZohoAccount(BaseSanitizedModel):
    account_id: str
    account_name: str
    account_code: Optional[str] = None
    is_active: bool
    account_type: str
    currency_id: Optional[str] = None
    currency_code: Optional[str] = None
    description: Optional[str] = None
    is_user_created: bool
    is_system_account: bool
    can_show_in_ze: bool
    include_in_vat_return: Optional[str] = None
    custom_fields: Optional[List[CustomField]] = None
    parent_account_id: Optional[str] = None
    parent_account_name: Optional[str] = None
    documents: Optional[List[str]] = None
    created_time: datetime.datetime
    last_modified_time: Optional[datetime.datetime] = None
    depth: int
    has_attachment: bool
    is_child_present: bool
    child_count: Optional[str] = None
    is_standalone_account: bool
