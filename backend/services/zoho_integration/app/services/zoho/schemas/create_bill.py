from pydantic import BaseModel
from typing import List, Optional
import datetime

from app.core.utils.base_models import BaseSanitizedModel


class Document(BaseModel):
    document_id: int
    file_name: str


class CustomField(BaseModel):
    index: int
    value: str


class Tag(BaseModel):
    tag_id: str
    tag_option_id: str


class ItemCustomField(BaseModel):
    label: str
    value: str
    custom_field_id: int
    index: Optional[int] = None


class LineItem(BaseSanitizedModel):
    name: str
    quantity: int
    rate: float
    account_id: str
    tax_id: str

    purchaseorder_item_id: Optional[str] = None
    line_item_id: Optional[str] = None
    item_id: Optional[str] = None
    description: Optional[str] = None
    hsn_or_sac: Optional[int] = None
    reverse_charge_tax_id: Optional[int] = None
    location_id: Optional[str] = None
    tds_tax_id: Optional[str] = None
    tax_treatment_code: Optional[str] = None
    tax_exemption_id: Optional[str] = None
    tax_exemption_code: Optional[str] = None
    item_order: Optional[int] = None
    product_type: Optional[str] = None
    acquisition_vat_id: Optional[str] = None
    reverse_charge_vat_id: Optional[str] = None
    unit: Optional[str] = None
    tags: Optional[List["Tag"]] = None
    is_billable: Optional[bool] = None
    project_id: Optional[str] = None
    customer_id: Optional[str] = None
    item_custom_fields: Optional[List["ItemCustomField"]] = None
    serial_numbers: Optional[List[str]] = None


class Tax(BaseModel):
    tax_id: str
    tax_name: str
    tax_amount: float


class Approver(BaseModel):
    approver_id: int
    order: int


class CreateZohoBillRequest(BaseSanitizedModel):
    vendor_id: str
    bill_number: str
    date: datetime.date
    tax_total: float
    sub_total: float
    total: float
    line_items: List[LineItem]
    notes: Optional[str] = None

    currency_id: Optional[str] = None
    vat_treatment: Optional[str] = None
    is_update_customer: Optional[bool] = None
    purchaseorder_ids: Optional[List[int]] = None
    documents: Optional[List[Document]] = None
    source_of_supply: Optional[str] = None
    destination_of_supply: Optional[str] = None
    place_of_supply: Optional[str] = None
    permit_number: Optional[str] = None
    gst_treatment: Optional[str] = None
    tax_treatment: Optional[str] = None
    gst_no: Optional[str] = None
    pricebook_id: Optional[int] = None
    reference_number: Optional[str] = None
    due_date: Optional[datetime.date] = None
    payment_terms: Optional[int] = None
    payment_terms_label: Optional[str] = None
    recurring_bill_id: Optional[str] = None
    exchange_rate: Optional[float] = None
    is_item_level_tax_calc: Optional[bool] = None
    is_inclusive_tax: Optional[bool] = None
    adjustment: Optional[float] = None
    adjustment_description: Optional[str] = None
    location_id: Optional[str] = None
    custom_fields: Optional[List[CustomField]] = None
    taxes: Optional[List[Tax]] = None
    terms: Optional[str] = None
    approvers: Optional[List[Approver]] = None
