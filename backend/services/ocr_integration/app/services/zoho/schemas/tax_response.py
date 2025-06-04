from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict
import datetime


class ZohoTax(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tax_id: str
    tax_name: str
    tax_percentage: float
    tax_type: str
    tax_specific_type: Optional[str] = None
    output_tax_account_name: str
    purchase_tax_account_name: str
    tax_account_id: str
    purchase_tax_account_id: str
    is_inactive: bool
    is_value_added: bool
    is_default_tax: bool
    is_editable: bool
    last_modified_time: datetime.datetime
    status: str

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
