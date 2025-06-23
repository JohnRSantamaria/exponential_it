from fastapi import APIRouter
from app.core.logging import logger


router = APIRouter()


@router.post("/")
async def base():
    """
    Clasifica un gasto usando un plan contable (ZohoAccount).
    """
    logger.debug("inicia")
    return {"message": "OK"}
