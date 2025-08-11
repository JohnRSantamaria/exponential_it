from fastapi import APIRouter, Form, File, UploadFile
from app.core.logging import logger

router = APIRouter()


@router.post("/")
async def base(recipient: str = Form(...), file: UploadFile = File(...)):
    logger.debug(f"Recipient: {recipient}")
    logger.debug(f"Archivo recibido: {file.filename}")

    # content = await file.read()
    # logger.debug(f"Tamaño del archivo: {len(content)} bytes")

    

    return {
        "message": "Archivo recibido correctamente",
        "recipient": recipient,
        "filename": file.filename,
    }
