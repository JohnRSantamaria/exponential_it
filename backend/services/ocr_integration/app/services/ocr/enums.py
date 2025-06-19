from enum import Enum


class InvoiceState(str, Enum):
    draft = "draft"
    open = "open"
    paid = "paid"
    cancel = "cancel"
