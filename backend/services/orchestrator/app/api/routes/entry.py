from fastapi import APIRouter, Form, File, UploadFile

from app.services.taggun.main import handle_invoice_scan


router = APIRouter()


@router.post("/")
async def base(recipient: str = Form(...), file: UploadFile = File(...)):
    """Extrae y da formato a los datos de la imagenes."""
    return await handle_invoice_scan(recipient=recipient, file=file)
