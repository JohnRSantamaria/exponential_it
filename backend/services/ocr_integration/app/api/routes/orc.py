from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import required_service

from app.services.ocr.validator import valid_json
from app.services.admin.schemas import UserDataSchema
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
    data = valid_json(payload)
    

    print(data)

    # main_fields = proces_document(payload=payload, file=file, cif=cif)
