from typing import Dict, Optional

import datetime

from app.core.utils.base_models import BaseSanitizedModel


class ZohoTax(BaseSanitizedModel):
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
