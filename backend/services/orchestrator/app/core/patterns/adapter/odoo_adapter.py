from decimal import Decimal
from typing import Iterable
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
        logger.debug(f"url {url} \ncompany_vat:{self.company_vat}")

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
    async def attach_file_to_bill(self, bill_id, file, file_content):
        url = f"{self.path}/attachment?invoice_id={bill_id}"
        logger.info(url)

        headers = {"x-client-vat": self.company_vat}
        files = {"file": (file.filename, file_content, file.content_type)}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            reponse = await client.post(
                url=url,
                headers=headers,
                files=files,
            )
        return reponse.json()

    @error_interceptor
    async def get_the_total_of_the_final_invoice(self, invoice_id):
        url = f"{self.path}/invoice-total?invoice_id={invoice_id}"
        logger.info(url)

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url=url, headers=headers)

        return response.json()

    @error_interceptor
    async def delete_final_invoice(self, invoice_id):
        url = f"{self.path}/invoice?invoice_id={invoice_id}"

        headers = {"x-client-vat": self.company_vat}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(url=url, headers=headers)
        return response.json()

    @error_interceptor
    async def get_withholding_tax_id(self, amount: float) -> int | None:
        """
        GET {path}/get-tax-id?amount=-15.0
        Retorna el ID (int) o None si tu servicio no encuentra mapeo.
        """
        # Normaliza a string decimal para evitar artefactos de float en el querystring
        amount_str = str(Decimal(str(amount)))  # ej: -15.0

        url = f"{self.path}/get-tax-id?amount={amount_str}"
        headers = {"x-client-vat": self.company_vat}

        logger.debug(f"Buscando la retencion {amount_str} en : {url}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url=url, headers=headers)
        return response.json()
