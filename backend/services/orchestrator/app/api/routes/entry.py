from fastapi import APIRouter, Form, File, UploadFile, status
from typing import List
from app.services.taggun.main import handle_invoice_scan, handle_multiple_invoice_scans

router = APIRouter()


@router.post("/", name="Procesar una factura", status_code=status.HTTP_201_CREATED)
async def base(recipient: str = Form(...), file: UploadFile = File(...)):
    return await handle_invoice_scan(recipient=recipient, file=file)


@router.post(
    "/bulk", name="Procesar múltiples facturas", status_code=status.HTTP_201_CREATED
)
async def bulk(recipient: str = Form(...), files: List[UploadFile] = File(...)):
    return await handle_multiple_invoice_scans(recipient=recipient, files=files)
