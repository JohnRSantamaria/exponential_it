from typing import List, Union
from fastapi import Depends, HTTPException

from app.core.security import get_current_user
from app.services.admin.schemas import UserDataSchema


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
