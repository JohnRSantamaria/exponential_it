import httpx
from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from app.core.patterns.adapter.account_provider import AccountingProvider
from app.services.odoo.interceptor import error_interceptor
from app.core.logging import logger
from exponential_core.odoo.schemas import (
    SupplierCreateSchema,
    AddressCreateSchema,
    ProductCreateSchema,
    InvoiceCreateSchema,
)


class OdooAdapter(AccountingProvider):
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
    async def create_vendor(self, payload: SupplierCreateSchema):
        url = f"{self.path}/create-supplier"
        logger.debug(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url=url,
                headers=headers,
                json=payload.model_dump(mode="json", exclude_none=True),
            )

        return response.json()

    @error_interceptor
    async def create_address(self, payload: AddressCreateSchema):
        url = f"{self.path}/create-address"
        logger.debug(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url=url,
                headers=headers,
                json=payload.model_dump(mode="json", exclude_none=True),
            )

        return response.json()

    @error_interceptor
    async def get_all_taxes(self):
        url = f"{self.path}/get-all-tax-id"
        logger.debug(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url=url, headers=headers)

        return response.json()

    @error_interceptor
    async def create_product(self, payload: ProductCreateSchema):
        url = f"{self.path}/create-product"
        logger.debug(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url=url,
                headers=headers,
                json=payload.model_dump(
                    mode="json",
                    exclude_none=True,
                ),
            )
        return response.json()

    @error_interceptor
    async def create_bill(self, payload: InvoiceCreateSchema):
        url = f"{self.path}/register-invoice"
        logger.debug(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            reponse = await client.post(
                url=url,
                headers=headers,
                json=payload.model_dump(
                    mode="json",
                    exclude_none=True,
                ),
            )
        return reponse.json()
