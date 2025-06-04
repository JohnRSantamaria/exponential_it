from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Optional
import datetime


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
    custom_field_id: int
    index: int
    value: str
    label: str


class LineItem(BaseModel):
    purchaseorder_item_id: str
    line_item_id: str
    item_id: str
    name: str
    account_id: str
    description: str
    rate: float
    hsn_or_sac: int
    reverse_charge_tax_id: int
    location_id: str
    quantity: int
    tax_id: str
    tds_tax_id: str
    tax_treatment_code: str
    tax_exemption_id: str
    tax_exemption_code: str
    item_order: int
    product_type: str
    acquisition_vat_id: str
    reverse_charge_vat_id: str
    unit: str
    tags: List[Tag]
    is_billable: bool
    project_id: str
    customer_id: str
    item_custom_fields: List[ItemCustomField]
    serial_numbers: List[str]


class Tax(BaseModel):
    tax_id: str
    tax_name: str
    tax_amount: float


class Approver(BaseModel):
    approver_id: int
    order: int


class CreateZohoBillRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vendor_id: str
    currency_id: str
    vat_treatment: Optional[str] = None
    is_update_customer: Optional[bool] = None
    purchaseorder_ids: Optional[List[int]] = None
    bill_number: str
    documents: Optional[List[Document]] = None
    source_of_supply: Optional[str] = None
    destination_of_supply: Optional[str] = None
    place_of_supply: Optional[str] = None
    permit_number: Optional[str] = None
    gst_treatment: Optional[str] = None
    tax_treatment: Optional[str] = None
    gst_no: Optional[str] = None
    pricebook_id: Optional[str] = None
    reference_number: Optional[str] = None
    date: datetime.date
    due_date: datetime.date
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
    line_items: List[LineItem]
    taxes: Optional[List[Tax]] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    approvers: Optional[List[Approver]] = None

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
