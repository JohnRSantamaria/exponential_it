from typing import List, Union
from fastapi import Depends, HTTPException, Header

from app.core.security import get_current_user
from app.services.admin.schemas import UserDataSchema
from app.services.odoo.client import AsyncOdooClient
from app.services.odoo.secrets import SecretsService


def required_service(required_services: List[Union[int, str]]):

    async def dependency(user_data: dict = Depends(get_current_user)):
        active_raw = user_data.get("active_subscriptions", [])

        try:
            required_set = set(map(int, required_services))
            active_set = set(map(int, active_raw))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail="Error al procesar servicios requeridos o suscripciones activas.",
            )

        missing = list(required_set - active_set)

        if missing:
            raise HTTPException(
                status_code=403,
                detail="No cuenta con acceso al servicio requerido.",
            )

        return UserDataSchema(**user_data)

    return dependency


def get_client_vat(x_client_vat: str = Header(...)) -> str:
    return x_client_vat


async def get_company(client_vat: str = Depends(get_client_vat)) -> AsyncOdooClient:

    secrets_service = await SecretsService(company_vat=client_vat).load()

    client = AsyncOdooClient(
        url=secrets_service.get_url(),
        db=secrets_service.get_db(),
        username=secrets_service.get_username(),
        api_key=secrets_service.get_api_key(),
    )

    await client.authenticate()

    return client
