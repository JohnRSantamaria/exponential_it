from typing import List
from fastapi import APIRouter, Body
from app.core.exceptions.types import CustomAppException
from app.services.zoho.schemas.chart_of_accounts_response import ZohoAccount


router = APIRouter()


@router.post("/classify-expense")
async def classify_expense(
    text: str = Body(..., embed=True),
    chart_of_accounts: List[ZohoAccount] = Body(...),
):
    """
    Clasifica un gasto usando un plan contable (ZohoAccount).
    """

    raise CustomAppException(
        status_code=503,
        message="service is currently unavailable",
    )
