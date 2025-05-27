from fastapi import APIRouter
from app.core.types import CustomAppException

router = APIRouter(prefix="/odoo", tags=["odoo"])


@router.get("/health")
async def health_check():
    """
    Endpoint de verificación de salud para Odoo.
    Retorna un mensaje simple indicando que el servicio está activo.
    """
    data = 0 / 0
    raise CustomAppException(
        status_code=503,
        message="Odoo service is currently unavailable",
    )


@router.get("/version")
async def get_version():
    """
    Endpoint para obtener la versión de Odoo.
    Retorna un mensaje con la versión del servicio Odoo.
    """
    return {"version": "Odoo 16.0", "status": "Odoo service is running"}


@router.get("/info")
async def get_info():
    """
    Endpoint para obtener información del servicio Odoo.
    Retorna un mensaje con información básica del servicio Odoo.
    """
    return {
        "service": "Odoo",
        "version": "16.0",
        "description": "Odoo is an open-source suite of business applications.",
        "status": "Odoo service is running",
    }
