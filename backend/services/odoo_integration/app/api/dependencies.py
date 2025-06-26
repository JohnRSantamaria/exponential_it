from typing import List, Union
from fastapi import Depends, HTTPException, Header

from app.core.security import get_current_user
from app.services.admin.schemas import UserDataSchema
from app.services.odoo.factory import OdooCompanyFactory
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


def get_company(client_vat: str = Depends(get_client_vat)) -> OdooCompanyFactory:
    secrets = SecretsService(client_vat)
    factory = OdooCompanyFactory()
    factory.register_company(
        client_vat=client_vat,
        url=secrets.get_url(),
        db=secrets.get_db(),
        username=secrets.get_username(),
        api_key=secrets.get_api_key(),
    )
    return factory.get_company(client_vat)
