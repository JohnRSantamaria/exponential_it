from pydantic import BaseModel
from typing import List, Optional
import datetime

from app.core.utils.base_models import BaseSanitizedModel


class LineItem(BaseSanitizedModel):
    name: str
    quantity: int
    rate: float
    account_id: str
    tax_id: str


class CreateZohoBillRequest(BaseSanitizedModel):
    vendor_id: str
    bill_number: str
    date: datetime.date
    tax_total: float
    sub_total: float
    total: float
    line_items: List[LineItem]
    notes: Optional[str] = None
