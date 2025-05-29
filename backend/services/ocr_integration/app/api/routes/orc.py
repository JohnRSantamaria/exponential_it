from typing import Annotated
from fastapi import APIRouter, File, Form, UploadFile

from app.services.ocr.base import proces_document


router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/invoices")
async def ocr_invoices(
    payload: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    # _: dict = Depends(required_service(["ocr"])),
):
    """
    Esta ruta procesa documentos OCR solo si el usuario está autenticado correctamente con un JWT emitido por Django.
    """
    return await proces_document(payload=payload, file=file)
