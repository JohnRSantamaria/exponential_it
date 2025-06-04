import datetime
from pydantic import BaseModel
from typing import Dict, Optional, List, Union


class ZohoBill(BaseModel):
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
    is_opening_balance: Union[bool, str]  # podría ser un booleano mal mapeado
    attachment_name: Optional[str] = None
    has_attachment: bool
    tags: List[str]
    is_uber_bill: bool
    is_tally_bill: bool
    entity_type: str
    client_viewed_time: Optional[str] = None  # Puede ser "" o timestamp
    is_viewed_by_client: bool
    is_bill_reconciliation_violated: bool

    def clean_payload(self) -> Dict:
        """
        Retorna un dict limpio, excluyendo campos None, vacíos, o listas vacías.
        """

        def is_useful(value):
            if value is None:
                return False
            if isinstance(value, str) and value.strip() == "":
                return False
            if isinstance(value, list) and len(value) == 0:
                return False
            return True

        raw = self.model_dump(exclude_none=True)
        return {k: v for k, v in raw.items() if is_useful(v)}
