from fastapi import APIRouter, Depends

from app.api.dependencies import required_service
from app.core.exceptions.types import CustomAppException
from app.services.admin.schemas import UserDataSchema


router = APIRouter(prefix="/zoho", tags=["zoho"])


@router.get("/")
async def health_check(
    user_data: UserDataSchema = Depends(required_service(["1"])),
):
    """
    Endpoint de verificación de salud para Odoo.
    Retorna un mensaje simple indicando que el servicio está activo.
    """

    print(user_data)
    raise CustomAppException(
        status_code=503,
        message="service is currently unavailable",
    )
