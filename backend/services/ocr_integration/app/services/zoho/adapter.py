import httpx
from app.core.interface.account_provider import AccountingProvider
from app.core.interface.provider_config import ProviderConfig
from app.services.ocr.schemas import Invoice, Supplier
from app.services.zoho.builders import (
    build_zoho_contact_payload,
    build_zoho_invoice_payload,
)
from app.services.zoho.wrappers.zoho_error_interceptor import error_interceptor


class ZohoAdapter(AccountingProvider):
    def __init__(self, config: ProviderConfig):
        self.path = config.path

    @error_interceptor
    async def get_all_contacts(self):
        path = f"{self.path}/contacts"

        async with httpx.AsyncClient() as client:
            response = await client.get(path)
        return response.json()

    @error_interceptor
    async def create_vendor(self, vendor: Supplier):
        path = f"{self.path}/contact"
        payload = build_zoho_contact_payload(supplier=vendor)

        async with httpx.AsyncClient() as client:
            response = await client.post(path, json=payload.clean_payload())

        return response.json()

    @error_interceptor
    async def get_all_bills(self):
        path = f"{self.path}/bills"

        async with httpx.AsyncClient() as client:
            response = await client.get(path)
        return response.json()

    @error_interceptor
    async def get_all_taxes(self):
        path = f"{self.path}/taxes"

        async with httpx.AsyncClient() as client:
            response = await client.get(path)
        return response.json()

    @error_interceptor
    async def create_bill(self, bill: Invoice):
        payload = build_zoho_invoice_payload(invoice=bill)
