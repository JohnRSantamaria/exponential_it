from typing import List
from fastapi import Depends, HTTPException

from app.core.security import get_current_user
from app.services.admin.schemas import UserDataSchema


def required_service(required_services: List[int]) -> UserDataSchema:

    async def dependency(user_data: dict = Depends(get_current_user)):

        active_ids = user_data.get("active_subscriptions", [])
        missing = [s for s in required_services if s not in active_ids]

        if len(missing) > 0:
            raise HTTPException(
                status_code=403,
                detail=f"No cuenta con acceso al servicio",
            )
        return UserDataSchema(**user_data)

    return dependency
