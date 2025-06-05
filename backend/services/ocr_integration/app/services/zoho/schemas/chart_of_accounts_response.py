from typing import Optional, List
from pydantic import BaseModel

from app.core.utils.base_models import BaseSanitizedModel


class ZohoAccountResponse(BaseSanitizedModel):
    account_id: str
    account_name: str
    account_code: Optional[str] = None
    account_type: str
    description: Optional[str] = None
    is_user_created: bool
    is_system_account: bool
    is_active: bool
    can_show_in_ze: bool
    parent_account_id: Optional[str] = None
    parent_account_name: Optional[str] = None
    depth: int
    has_attachment: bool
    is_child_present: bool
    child_count: Optional[str] = None
    documents: List[dict]
    created_time: str
    is_standalone_account: bool
    last_modified_time: str
