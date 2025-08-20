from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.core.logging import logger
from exponential_core.exceptions import CustomAppException

from app.services.claude.client import invoice_formater

router = APIRouter()


@router.post("/line-items")
async def extract_invoice_items(file: UploadFile = File(...)):
    """
    Endpoint para extraer elementos de línea de una factura (PDF o imagen)
    """
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No se proporcionó archivo")

        # Validar que sea PDF o imagen
        allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
        file_extension = file.filename.lower()

        if not any(file_extension.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"El archivo {file.filename} debe ser PDF o imagen (JPG, PNG, WEBP)",
            )

        logger.info(f"🚀 Iniciando procesamiento de archivo: {file.filename}")

        # Procesar el archivo
        result = await invoice_formater(file)

        return result

    except CustomAppException as e:
        logger.error(f"❌ Error de aplicación: {e.message}")
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error interno del servidor: {str(e)}"
        )
