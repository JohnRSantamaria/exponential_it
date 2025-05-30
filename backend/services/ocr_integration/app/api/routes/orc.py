from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import required_service


from app.services.ocr.parser_ocr import parser_invoice, parser_supplier
from app.services.ocr.validator import valid_json
from app.services.admin.schemas import UserDataSchema
from app.services.ocr.extractor import InvoiceExtractor
from app.services.admin.credentials import get_credential_by_key

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/invoices")
async def ocr_invoices(
    payload: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    user_data: UserDataSchema = Depends(required_service(["1"])),
):
    """
    Esta ruta procesa documentos OCR solo si el usuario está autenticado correctamente con un JWT emitido por Django.
    """
    cif = get_credential_by_key(user_id=user_data.user_id, key="CIF")

    ocr_data = valid_json(payload)

    invoice = parser_invoice(cif=cif, ocr_data=ocr_data)
    supplier = parser_supplier(cif=cif, ocr_data=ocr_data)

    return invoice.model_dump(mode="json")
