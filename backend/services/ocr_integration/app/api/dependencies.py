from typing import List
from fastapi import Depends, HTTPException

from app.core.security import get_current_user


def required_service(required_services: List[str]):

    async def dependency(user_data: dict = Depends(get_current_user)):

        active = user_data.get("active_subscriptions", [])
        missing = [s for s in required_services if s not in active]

        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"El servicio {missing} no esta activo.",
            )
        return user_data

    return dependency
