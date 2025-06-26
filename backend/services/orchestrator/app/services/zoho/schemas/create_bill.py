from typing import List, Optional
from pydantic import BaseModel
from datetime import date


class LineItem(BaseModel):
    name: str
    quantity: int
    rate: float
    account_id: str
    tax_id: str


class CreateZohoBillRequest(BaseModel):
    vendor_id: str
    bill_number: str
    date: date
    tax_total: float
    sub_total: float
    total: float
    line_items: List[LineItem]
    notes: Optional[str] = None
