from pydantic import BaseModel
from typing import Optional, List, Dict

from app.core.utils.base_models import BaseSanitizedModel


class CustomField(BaseModel):
    label: str
    value: str
    customfield_id: str
    index: Optional[int] = None


class ZohoContactResponse(BaseSanitizedModel):
    contact_id: str
    contact_name: str
    customer_name: str
    vendor_name: str
    company_name: str
    website: str
    language_code: str
    language_code_formatted: str
    contact_type: str
    contact_type_formatted: str
    status: str
    customer_sub_type: str
    source: str
    is_linked_with_zohocrm: bool
    payment_terms: int
    payment_terms_label: str
    currency_id: str
    twitter: str
    facebook: str
    currency_code: str
    outstanding_receivable_amount: float
    outstanding_receivable_amount_bcy: float
    outstanding_payable_amount: float
    outstanding_payable_amount_bcy: float
    unused_credits_receivable_amount: float
    unused_credits_receivable_amount_bcy: float
    unused_credits_payable_amount: float
    unused_credits_payable_amount_bcy: float
    first_name: str
    last_name: str
    email: str
    phone: str
    mobile: str
    portal_status: str
    portal_status_formatted: str
    created_time: str
    created_time_formatted: str
    last_modified_time: str
    last_modified_time_formatted: str
    custom_fields: Optional[List[CustomField]] = None
    cf_cif: Optional[str] = None
    cf_cif_unformatted: Optional[str] = None
    custom_field_hash: Optional[Dict[str, str]] = None
    tags: List[str]
    ach_supported: bool
    has_attachment: bool
