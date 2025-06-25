from typing import List
from fastapi import APIRouter, Body
from app.core.logging import logger
from app.services.openai.account_classifier import classify_account
from app.services.zoho.schemas.chart_of_accounts_response import ZohoAccount

router = APIRouter()


@router.post("/classify-expense")
async def classify_expense(
    text: str = Body(..., embed=True),
    chart_of_accounts: str = Body(...),
):
    """
    Clasifica un gasto usando un plan contable (ZohoAccount).
    """
    logger.info("Clasificando un gasto segun las el cuadro de cuentras de Zoho.")
    return await classify_account(text=text, chart=chart_of_accounts)
