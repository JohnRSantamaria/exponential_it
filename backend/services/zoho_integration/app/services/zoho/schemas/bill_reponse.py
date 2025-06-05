import datetime
from typing import Dict, Optional, List, Union

from app.core.utils.base_models import BaseSanitizedModel


class ZohoBill(BaseSanitizedModel):
    bill_id: str
    vendor_id: str
    vendor_name: str
    status: str
    color_code: Optional[str] = None
    current_sub_status_id: Optional[str] = None
    current_sub_status: Optional[str] = None
    bill_number: str
    reference_number: Optional[str] = None
    date: datetime.date
    due_date: datetime.date
    due_days: str
    currency_id: str
    currency_code: str
    price_precision: int
    exchange_rate: float
    total: float
    tds_total: float
    balance: float
    unprocessed_payment_amount: float
    created_time: datetime.datetime
    last_modified_time: datetime.datetime
    is_opening_balance: Union[bool, str]
    attachment_name: Optional[str] = None
    has_attachment: bool
    tags: List[str]
    is_uber_bill: bool
    is_tally_bill: bool
    entity_type: str
    client_viewed_time: Optional[str] = None
    is_viewed_by_client: bool
    is_bill_reconciliation_violated: bool
