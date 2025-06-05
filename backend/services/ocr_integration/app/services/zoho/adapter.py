from fastapi import UploadFile
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
    async def create_vendor(self, vendor: Supplier):
        url = f"{self.path}/contact"
        payload = build_zoho_contact_payload(supplier=vendor)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload.clean_payload())

        return response.json()

    @error_interceptor
    async def create_bill(self, bill: Invoice):
        url = f"{self.path}/bill"
        payload = build_zoho_invoice_payload(invoice=bill)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload.clean_payload())

        return response.json()

    @error_interceptor
    async def get_all_contacts(self):
        url = f"{self.path}/contacts"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        return response.json()

    @error_interceptor
    async def get_all_bills(self):
        url = f"{self.path}/bills"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        return response.json()

    @error_interceptor
    async def attach_file_to_bill(
        self, bill_id: str, file: UploadFile, file_content: bytes
    ) -> dict:
        url = f"{self.path}/bill/{bill_id}/attachment"
        files = {"file": (file.filename, file_content, file.content_type)}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, files=files)
        return response.json()

    @error_interceptor
    async def get_chart_of_accounts(self):
        url = f"{self.path}/chart-of-accounts"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        return response.json()

    @error_interceptor
    async def get_all_taxes(self):
        url = f"{self.path}/taxes"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        return response.json()
