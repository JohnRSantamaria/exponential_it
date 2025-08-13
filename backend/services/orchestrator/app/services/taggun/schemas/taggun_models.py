from typing import Optional, Set
from datetime import date
from pydantic import BaseModel


class AddressSchema(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country_code: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class LineItemSchema(BaseModel):
    name: str
    quantity: float
    unit_price: float
    total_price: float


# 📦 Modelo parcial
class TaggunExtractedInvoiceBasic(BaseModel):
    partner_name: str
    partner_vat: str
    date: Optional[date]
    invoice_number: Optional[str]
    amount_total: float
    amount_tax: float
    amount_untaxed: float
    amount_discount: float


# 📦 Modelo completo heredando del básico
class TaggunExtractedInvoice(TaggunExtractedInvoiceBasic):
    address: AddressSchema
    line_items: list[LineItemSchema]
    tax_canditates: Optional[Set[float]]
