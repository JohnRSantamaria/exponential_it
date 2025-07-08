from fastapi import UploadFile
import httpx
from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from app.core.logging import logger
from app.core.patterns.adapter.account_provider import AccountingProvider
from app.services.zoho.interceptor import error_interceptor
from app.services.zoho.schemas.create_bill import CreateZohoBillRequest
from app.services.zoho.schemas.create_contact import CreateZohoContactRequest


class ZohoAdapter(AccountingProvider):
    def __init__(self, config: ProviderConfig):
        self.path = config.path
        self.company_vat = config.company_vat
        self.timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT_CONNECT,
            read=settings.HTTP_TIMEOUT_READ,
            write=settings.HTTP_TIMEOUT_WRITE,
            pool=settings.HTTP_TIMEOUT_POOL,
        )

    @error_interceptor
    async def create_vendor(self, payload: CreateZohoContactRequest):
        url = f"{self.path}/contact"
        logger.debug(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url=url,
                json=payload.model_dump(mode="json"),
                headers=headers,
            )

        return response.json()

    @error_interceptor
    async def create_bill(self, payload: CreateZohoBillRequest):
        url = f"{self.path}/bill"
        logger.info(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url=url,
                headers=headers,
                json=payload.model_dump(mode="json"),
            )

        return response.json()

    @error_interceptor
    async def get_all_contacts(self):
        url = f"{self.path}/contacts"
        logger.debug(f"Obteniendo contactos : {url}")

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url=url,
                headers=headers,
            )
        return response.json()

    @error_interceptor
    async def get_all_bills(self):
        url = f"{self.path}/bills"
        logger.info(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url=url,
                headers=headers,
            )
        return response.json()

    @error_interceptor
    async def attach_file_to_bill(
        self, bill_id: str, file: UploadFile, file_content: bytes
    ) -> dict:
        url = f"{self.path}/bill/{bill_id}/attachment"
        logger.info(url)

        headers = {"x-client-vat": self.company_vat}
        files = {"file": (file.filename, file_content, file.content_type)}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url=url,
                headers=headers,
                files=files,
            )
        return response.json()

    @error_interceptor
    async def get_chart_of_accounts(self):
        url = f"{self.path}/chart-of-accounts"
        logger.info(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url=url,
                headers=headers,
            )
        return response.json()

    @error_interceptor
    async def get_all_taxes(self):
        url = f"{self.path}/taxes"
        logger.info(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url=url,
                headers=headers,
            )
        return response.json()
