from typing import List
from fastapi import APIRouter, Body
from app.core.logging import logger
from app.services.openai.account_classifier import classify_account
from app.services.openai.schemas.classification_tax_request import ClasificacionRequest
from app.services.openai.tax_id_classifier import classify_tax_id
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
    logger.info("Clasificando un gasto segun las el cuadro de cuentas de Zoho.")
    return await classify_account(text=text, chart=chart_of_accounts)


@router.post("/classify-odoo-tax_id")
async def classify_odoo_tax_id(payload: ClasificacionRequest):
    """
    Clasifica los taxes disponibles dentro de Odoo, utlizando los datos recuperados a través
    del OCR.
    """
    logger.info("Clasificando taxes segun las cuentas diponibles de Odoo.")
    return await classify_tax_id(payload)
