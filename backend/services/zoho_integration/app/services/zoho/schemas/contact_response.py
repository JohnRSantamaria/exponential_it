from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict

from app.core.utils.base_models import BaseSanitizedModel


class CustomField(BaseModel):
    field_id: str
    customfield_id: str
    show_in_store: bool
    show_in_portal: bool
    is_active: bool
    index: int
    label: str
    show_on_pdf: bool
    edit_on_portal: bool
    edit_on_store: bool
    api_name: str
    show_in_all_pdf: bool
    value_formatted: Optional[str] = None
    search_entity: Optional[str] = None
    data_type: Optional[str] = None
    placeholder: Optional[str] = None
    value: Optional[str] = None
    is_dependent_field: bool


class Address(BaseModel):
    address_id: Optional[str] = None
    attention: Optional[str] = None
    address: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state_code: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    county: Optional[str] = None
    country_code: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None


class DefaultTemplates(BaseModel):
    statement_template_id: Optional[str] = None
    statement_template_name: Optional[str] = None
    invoice_template_id: Optional[str] = None
    invoice_template_name: Optional[str] = None
    bill_template_id: Optional[str] = None
    bill_template_name: Optional[str] = None
    estimate_template_id: Optional[str] = None
    estimate_template_name: Optional[str] = None
    creditnote_template_id: Optional[str] = None
    creditnote_template_name: Optional[str] = None
    paymentthankyou_template_id: Optional[str] = None
    paymentthankyou_template_name: Optional[str] = None
    invoice_email_template_id: Optional[str] = None
    invoice_email_template_name: Optional[str] = None
    estimate_email_template_id: Optional[str] = None
    estimate_email_template_name: Optional[str] = None
    creditnote_email_template_id: Optional[str] = None
    creditnote_email_template_name: Optional[str] = None
    paymentthankyou_email_template_id: Optional[str] = None
    paymentthankyou_email_template_name: Optional[str] = None
    payment_remittance_email_template_id: Optional[str] = None
    payment_remittance_email_template_name: Optional[str] = None


class VendorCurrencySummary(BaseModel):
    currency_id: Optional[str] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None
    price_precision: Optional[int] = None
    is_base_currency: Optional[bool] = None
    currency_name_formatted: Optional[str] = None
    outstanding_payable_amount: Optional[float] = None
    unused_credits_payable_amount: Optional[float] = None


class ZohoContact(BaseSanitizedModel):
    contact_id: str
    contact_name: str
    company_name: Optional[str] = None
    contact_tax_information: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    website: Optional[str] = None
    is_bcy_only_contact: Optional[bool] = None
    is_credit_limit_migration_completed: Optional[bool] = None
    language_code: Optional[str] = None
    language_code_formatted: Optional[str] = None
    contact_salutation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    invited_by: Optional[str] = None
    portal_status: Optional[str] = None
    is_client_review_asked: Optional[bool] = None
    has_transaction: Optional[bool] = None
    contact_type: str
    customer_sub_type: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    source: Optional[str] = None
    documents: Optional[List[dict]] = None
    twitter: Optional[str] = None
    facebook: Optional[str] = None
    is_crm_customer: Optional[bool] = None
    is_linked_with_zohocrm: Optional[bool] = None
    primary_contact_id: Optional[str] = None
    zcrm_vendor_id: Optional[str] = None
    crm_owner_id: Optional[str] = None
    payment_terms: Optional[int] = None
    payment_terms_label: Optional[str] = None
    payment_terms_id: Optional[str] = None
    credit_limit_exceeded_amount: Optional[float] = None
    currency_id: Optional[str] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None
    price_precision: Optional[int] = None
    exchange_rate: Optional[str] = None
    can_show_customer_ob: Optional[bool] = None
    can_show_vendor_ob: Optional[bool] = None
    opening_balance_amount: Optional[float] = None
    opening_balance_amount_bcy: Optional[str] = None
    outstanding_ob_receivable_amount: Optional[float] = None
    outstanding_ob_payable_amount: Optional[float] = None
    outstanding_receivable_amount: float
    outstanding_receivable_amount_bcy: float
    outstanding_payable_amount: float
    outstanding_payable_amount_bcy: float
    unused_credits_receivable_amount: float
    unused_credits_receivable_amount_bcy: float
    unused_credits_payable_amount: float
    unused_credits_payable_amount_bcy: float
    unused_retainer_payments: Optional[float] = None
    status: str
    payment_reminder_enabled: Optional[bool] = None
    is_sms_enabled: Optional[bool] = None
    is_consent_agreed: Optional[bool] = None
    consent_date: Optional[str] = None
    is_client_review_settings_enabled: Optional[bool] = None
    custom_fields: Optional[List[CustomField]] = None
    cf_cif: Optional[str] = None
    cf_cif_unformatted: Optional[str] = None
    custom_field_hash: Optional[Dict[str, str]] = None
    tax_id: Optional[str] = None
    tax_name: Optional[str] = None
    tax_percentage: Optional[str] = None
    tax_reg_label: Optional[str] = None
    tax_treatment: Optional[str] = None
    tax_reg_no: Optional[str] = None
    contact_category: Optional[str] = None
    sales_channel: Optional[str] = None
    ach_supported: bool
    portal_receipt_count: Optional[int] = None
    opening_balances: Optional[List[dict]] = None
    entity_address_id: Optional[str] = None
    billing_address: Optional[Address] = None
    shipping_address: Optional[Address] = None
    contact_persons: Optional[List[dict]] = None
    addresses: Optional[List[dict]] = None
    pricebook_id: Optional[str] = None
    pricebook_name: Optional[str] = None
    default_templates: Optional[DefaultTemplates] = None
    associated_with_square: Optional[bool] = None
    cards: Optional[List[dict]] = None
    checks: Optional[List[dict]] = None
    bank_accounts: Optional[List[dict]] = None
    vpa_list: Optional[List[dict]] = None
    notes: Optional[str] = None
    created_time: str
    created_date: Optional[str] = None
    created_by_name: Optional[str] = None
    last_modified_time: str
    tags: List[str]
    zohopeople_client_id: Optional[str] = None
    siret_number: Optional[str] = None
    company_id: Optional[str] = None
    label_for_company_id: Optional[str] = None
    vendor_currency_summaries: Optional[List[VendorCurrencySummary]] = None
    approvers_list: Optional[List[dict]] = None
    submitted_date: Optional[str] = None
    submitted_by: Optional[str] = None
    submitted_by_name: Optional[str] = None
    submitted_by_email: Optional[str] = None
    submitted_by_photo_url: Optional[str] = None
    submitter_id: Optional[str] = None
    approver_id: Optional[str] = None
    integration_references: Optional[List[dict]] = None
    customer_name: Optional[str] = None
    vendor_name: Optional[str] = None
    contact_type_formatted: Optional[str] = None
    portal_status_formatted: Optional[str] = None
    created_time_formatted: Optional[str] = None
    last_modified_time_formatted: Optional[str] = None
    has_attachment: Optional[bool] = None
