from pydantic import BaseModel
from typing import Optional, List, Union


class Address(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[Union[int, str]] = None
    country: Optional[str] = None
    fax: Optional[str] = None
    phone: Optional[str] = None


class CustomFieldInput(BaseModel):
    value: Optional[str] = None
    label: Optional[str] = None
    customfield_id: Optional[str] = None


class CreateZohoContactRequest(BaseModel):
    contact_name: str
    company_name: Optional[str] = None
    language_code: Optional[str] = None
    contact_type: Optional[str] = None
    currency_id: Optional[Union[str, int]] = None
    currency_code: Optional[str] = None
    customer_sub_type: Optional[str] = None
    billing_address: Optional[Address] = None
    custom_fields: Optional[List[CustomFieldInput]] = None
