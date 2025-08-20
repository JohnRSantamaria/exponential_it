# app/services/claude/routes.py
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.core.logging import logger

from exponential_core.cluadeai import InvoiceResponseSchema
from exponential_core.exceptions import CustomAppException
from app.services.claude.client import invoice_formater

router = APIRouter()

# Límite de tamaño (20 MB por defecto, ajústalo si lo necesitas)
MAX_FILE_BYTES = 20 * 1024 * 1024

ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}


def http_error(status_code: int, message: str, data: dict | None = None) -> None:
    """Helper para responder errores con formato uniforme."""
    raise HTTPException(
        status_code=status_code,
        detail={"message": message, "data": data or {}},
    )


@router.post("/line-items", response_model=InvoiceResponseSchema)
async def extract_invoice_items(file: UploadFile = File(...)):
    """
    Extrae elementos de línea de una factura (PDF o imagen).
    Respuestas de error SIEMPRE en el formato:
        HTTPException(detail={"message": <str>, "data": <dict>})
    """
    try:
        # Validación de presencia
        if not file:
            http_error(status.HTTP_400_BAD_REQUEST, "No file provided")

        # Validación de extensión
        fname = (file.filename or "").strip()
        ext = Path(fname).suffix.lower()
        if ext not in ALLOWED_EXTS:
            http_error(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                f"File '{fname}' must be PDF or image (JPG, PNG, WEBP)",
                {
                    "filename": fname,
                    "ext": ext,
                    "allowed_extensions": sorted(ALLOWED_EXTS),
                },
            )

        # Validación de content-type (best-effort; algunos clientes no lo envían bien)
        ctype = (file.content_type or "").lower()
        if ctype and ctype not in ALLOWED_MIME:
            http_error(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                f"Unsupported Content-Type '{ctype}' for '{fname}'",
                {
                    "filename": fname,
                    "content_type": ctype,
                    "allowed_mime": sorted(ALLOWED_MIME),
                },
            )

        # Validación de tamaño sin consumir el stream
        try:
            # SpooledTemporaryFile permite seek/tell
            file.file.seek(0, 2)  # fin
            size = file.file.tell()
            file.file.seek(0)  # reset para que el formater pueda leer
        except Exception:
            size = None

        if size is not None and size > MAX_FILE_BYTES:
            http_error(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"File '{fname}' exceeds the max size of {MAX_FILE_BYTES} bytes",
                {"filename": fname, "size": size, "max_bytes": MAX_FILE_BYTES},
            )

        logger.info(
            f"🚀 Processing file: {fname} (ctype={ctype or 'unknown'}, size={size or 'unknown'})"
        )
        # Delega toda la lógica de parsing/normalización/validación
        return await invoice_formater(file)

    except CustomAppException as e:
        # Excepciones propias con mensaje y data estructurada
        logger.error(f"❌ App error: {e.message} | data={getattr(e, 'data', {})}")
        http_error(
            getattr(e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR),
            e.message,
            getattr(e, "data", {}),
        )

    except HTTPException:
        # Ya está formateado como HTTPException
        raise

    except Exception as e:
        # Cualquier otro error inesperado
        logger.exception(
            f"❌ Unexpected error while processing '{getattr(file, 'filename', '<no-name>')}'"
        )
        http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error",
            {"reason": str(e)},
        )
