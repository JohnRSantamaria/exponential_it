from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class InvoiceState(str, Enum):
    draft = "draft"
    open = "open"
    paid = "paid"
    cancel = "cancel"
