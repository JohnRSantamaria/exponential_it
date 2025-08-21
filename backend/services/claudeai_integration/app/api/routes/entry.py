# app/services/claude/routes.py
import base64
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.core.logging import logger

from exponential_core.cluadeai import InvoiceResponseSchema
from exponential_core.exceptions import CustomAppException
from app.services.claude.client import invoice_formater
from app.services.claude.utils.helpers import (
    ALLOWED_EXTS,
    ALLOWED_MIME,
    MAX_FILE_BYTES,
    _detect_media_type,
    http_error,
)
from app.services.claude.withholdings import (
    RetentionHTTPResponse,
    _call_claude_retention,
    _complete_retention_fields,
)

router = APIRouter()


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


@router.post("/retention", response_model=RetentionHTTPResponse)
async def detect_retention_by_ai(file: UploadFile = File(...)):
    """
    Busca explícitamente RETENCIONES en el documento usando IA (Claude) y devuelve:
      - has_retention (bool)
      - total_retention (Decimal, abs, 2 decimales)
      - retention_percent (Decimal, 2 decimales)
    La IA debe escanear el PDF/imagen por textos como "Retención", "IRPF", "Retención Fiscal", "Withholding".
    """
    try:
        # Validaciones de archivo
        if not file:
            http_error(status.HTTP_400_BAD_REQUEST, "No file provided")

        fname = (file.filename or "").strip()
        ext = Path(fname).suffix.lower()
        if ext not in ALLOWED_EXTS:
            http_error(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                f"File '{fname}' must be PDF or image",
                {
                    "filename": fname,
                    "ext": ext,
                    "allowed_extensions": sorted(ALLOWED_EXTS),
                },
            )

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

        try:
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
        except Exception:
            size = None

        if size is not None and size > MAX_FILE_BYTES:
            http_error(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"File '{fname}' exceeds the max size of {MAX_FILE_BYTES} bytes",
                {"filename": fname, "size": size, "max_bytes": MAX_FILE_BYTES},
            )

        logger.info(
            f"🔎 Detecting retention (by AI) for: {fname} (ctype={ctype or 'unknown'}, size={size or 'unknown'})"
        )

        # Leer bytes y codificar base64
        try:
            file_bytes = await file.read()
        finally:
            try:
                file.file.seek(
                    0
                )  # opcional: reset por si usas el file de nuevo después
            except Exception:
                pass

        file_b64 = base64.b64encode(file_bytes).decode("utf-8")
        media_type = _detect_media_type(file)

        # Llamada a Claude enfocada SOLO en retenciones
        ai_result = await _call_claude_retention(
            file_b64=file_b64, media_type=media_type
        )

        # Completar y normalizar campos
        response_obj = _complete_retention_fields(ai_result)
        return response_obj

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"❌ Unexpected error while processing '{getattr(file, 'filename', '<no-name>')}'"
        )
        http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error",
            {"reason": str(e)},
        )
