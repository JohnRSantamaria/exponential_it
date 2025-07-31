from fastapi import Depends, Header

from app.services.odoo.client import AsyncOdooClient
from app.services.odoo.secrets import SecretsService


def get_client_vat(x_client_vat: str = Header(...)) -> str:
    return x_client_vat


async def get_company(client_vat: str = Depends(get_client_vat)) -> AsyncOdooClient:

    secrets_service = await SecretsService(company_vat=client_vat).load()

    client = AsyncOdooClient(
        url=secrets_service.get_url(),
        db=secrets_service.get_db(),
        username=secrets_service.get_username(),
        api_key=secrets_service.get_api_key(),
        company_id=secrets_service.get_company_id(),
    )

    await client.authenticate()

    return client
