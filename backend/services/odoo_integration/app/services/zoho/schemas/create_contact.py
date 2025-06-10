from pydantic import BaseModel, Field
from typing import Optional, List, Union, Dict


class Address(BaseModel):
    attention: Optional[str] = None
    address: Optional[str] = None
    street2: Optional[str] = None
    state_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[Union[int, str]] = None
    country: Optional[str] = None
    fax: Optional[str] = None
    phone: Optional[str] = None


class Tag(BaseModel):
    tag_id: Union[int, str]
    tag_option_id: Union[int, str]


class CustomFieldInput(BaseModel):
    value: Optional[str] = None
    label: Optional[str] = None
    customfield_id: Optional[str] = None


class DefaultTemplates(BaseModel):
    invoice_template_id: Optional[int] = None
    estimate_template_id: Optional[int] = None
    creditnote_template_id: Optional[int] = None
    purchaseorder_template_id: Optional[int] = None
    salesorder_template_id: Optional[int] = None
    retainerinvoice_template_id: Optional[int] = None
    paymentthankyou_template_id: Optional[int] = None
    retainerinvoice_paymentthankyou_template_id: Optional[int] = None
    invoice_email_template_id: Optional[int] = None
    estimate_email_template_id: Optional[int] = None
    creditnote_email_template_id: Optional[int] = None
    purchaseorder_email_template_id: Optional[int] = None
    salesorder_email_template_id: Optional[int] = None
    retainerinvoice_email_template_id: Optional[int] = None
    paymentthankyou_email_template_id: Optional[int] = None
    retainerinvoice_paymentthankyou_email_template_id: Optional[int] = None


class OpeningBalance(BaseModel):
    location_id: str
    exchange_rate: float
    opening_balance_amount: float


class CreateZohoContactRequest(BaseModel):
    contact_name: str
    company_name: Optional[str] = None
    website: Optional[str] = None
    language_code: Optional[str] = None
    contact_type: Optional[str] = None
    customer_sub_type: Optional[str] = None
    credit_limit: Optional[float] = None
    tags: Optional[List[Tag]] = None
    is_portal_enabled: Optional[bool] = None
    currency_id: Optional[Union[str, int]] = None
    currency_code: Optional[str] = None
    payment_terms: Optional[int] = None
    payment_terms_label: Optional[str] = None
    notes: Optional[str] = None
    billing_address: Optional[Address] = None
    shipping_address: Optional[Address] = None
    contact_persons: Optional[Union[str, List[Dict]]] = None
    default_templates: Optional[DefaultTemplates] = None
    custom_fields: Optional[List[CustomFieldInput]] = None
    opening_balances: Optional[List[OpeningBalance]] = None
    vat_reg_no: Optional[str] = None
    owner_id: Optional[Union[str, int]] = None
    tax_reg_no: Optional[Union[str, int]] = None
    tax_exemption_certificate_number: Optional[str] = None
    country_code: Optional[str] = None
    vat_treatment: Optional[str] = None
    tax_treatment: Optional[str] = None
    tax_regime: Optional[str] = None
    legal_name: Optional[str] = None
    is_tds_registered: Optional[bool] = None
    place_of_contact: Optional[str] = None
    gst_no: Optional[str] = None
    gst_treatment: Optional[str] = None
    tax_authority_name: Optional[str] = None
    avatax_exempt_no: Optional[str] = None
    avatax_use_code: Optional[str] = None
    tax_exemption_id: Optional[Union[str, int]] = None
    tax_exemption_code: Optional[str] = None
    tax_authority_id: Optional[Union[str, int]] = None
    tax_id: Optional[Union[str, int]] = None
    tds_tax_id: Optional[str] = None
    is_taxable: Optional[bool] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    track_1099: Optional[bool] = None
    tax_id_type: Optional[str] = None
    tax_id_value: Optional[str] = None

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
