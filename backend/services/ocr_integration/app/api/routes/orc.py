from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.api.dependencies import required_service
from app.core.logger import configure_logging
from app.services.ocr.validator import valid_json
from app.services.zoho.process import zoho_process
from app.services.admin.schemas import UserDataSchema
from app.services.admin.credentials import get_credential_by_key
from app.services.ocr.parser_ocr import parser_invoice, parser_supplier

logger = configure_logging()
router = APIRouter()


@router.post("/")
async def ocr_invoices(
    payload: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    user_data: UserDataSchema = Depends(required_service([1])),
):
    """
    Esta ruta procesa documentos OCR solo si el usuario está autenticado correctamente con un JWT emitido por Django.
    """
    logger.info("Proceso de Optical Character Recognition (OCR) iniciado.")
    cif = get_credential_by_key(user_id=user_data.user_id, key="CIF")

    ocr_data = valid_json(payload)
    invoice = parser_invoice(cif=cif, ocr_data=ocr_data)
    supplier = parser_supplier(cif=cif, ocr_data=ocr_data)

    file_content = await file.read()

    await zoho_process(
        invoice=invoice,
        supplier=supplier,
        file=file,
        file_content=file_content,
    )

    logger.info("Proceso de Optical Character Recognition (OCR) finalizado.")

    return Response(status_code=201)
