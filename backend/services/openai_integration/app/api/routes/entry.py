from typing import Optional
from fastapi import APIRouter, Body, File, Form, UploadFile
from app.core.logging import logger
from app.services.openai.account_classifier import classify_account
from app.services.openai.parser_document import extract_data_from_invoice
from app.services.openai.schemas.classification_tax_request import ClasificacionRequest
from app.services.openai.search_by_cif import search_cif_by_partner
from app.services.openai.tax_id_classifier import classify_tax_id
from exponential_core.openai import InvoiceTotalsSchema

from app.services.openai.tax_id_extractor import (
    PartnerTaxIdSchema,
    extract_partner_taxid,
)

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


@router.post("/search_cif_by_partner")
async def search_partner(
    partner_name: str = Body(..., embed=True),
):
    """
    Busca el CIF de una empresa dado su nombre (enviado en el body).
    Si no se encuentra, devuelve {"CIF": "0"}.
    """
    return await search_cif_by_partner(partner_name=partner_name)


@router.post("/extract-invoice", response_model=InvoiceTotalsSchema)
async def parser_invoice(file: UploadFile = File(...)):
    """
    Recibe un PDF y devuelve:
    - subtotal, tax_amount, discount_amount, total, tax_rate_percent
    - evidencias (snippets)
    Valida aritmética y, si el PDF es digital y está habilitado, presencia de evidencias.
    """
    result = await extract_data_from_invoice(file)

    return {
        "currency": result.currency,
        "subtotal": result.subtotal.model_dump(),
        "tax_amount": result.tax_amount.model_dump(),
        "discount_amount": result.discount_amount.model_dump(),
        "total": result.total.model_dump(),
        "tax_rate_percent": str(result.tax_rate_percent),
        "withholding_amount": result.withholding_amount.model_dump(),
        "withholding_rate_percent": str(result.withholding_rate_percent),
        "evidence": result.evidence,
        "notes": result.notes,
    }


@router.post("/extract-partner-taxid", response_model=PartnerTaxIdSchema)
async def extract_patner(
    client_tax_id: Optional[str] = Form(
        None, description="CIF/NIF/VAT del cliente para excluir"
    ),
    file: UploadFile = File(...),
):
    result = await extract_partner_taxid(client_tax_id=client_tax_id, file=file)
    
    return result.model_dump(mode="json")
