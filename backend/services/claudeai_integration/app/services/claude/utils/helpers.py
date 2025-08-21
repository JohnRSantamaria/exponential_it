from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException, UploadFile


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


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        value = str(value)
    if isinstance(value, str):
        v = value.strip()
        if v == "":
            return None
        # Normaliza "1,234.56" o "1.234,56"
        if "," in v and "." in v:
            if v.find(",") < v.find("."):
                v = v.replace(",", "")
            else:
                v = v.replace(".", "").replace(",", ".")
        else:
            if "," in v:
                v = v.replace(",", ".")
        try:
            return Decimal(v)
        except InvalidOperation:
            return None
    return None


def _quantize_2(v: Decimal | None) -> Optional[Decimal]:
    return (
        v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if v is not None else None
    )


def _detect_media_type(file: UploadFile) -> str:
    # Usamos content_type si viene bien, si no, por extensión
    ctype = (file.content_type or "").lower()
    if ctype in ALLOWED_MIME:
        return ctype

    ext = Path((file.filename or "")).suffix.lower()
    if ext == ".pdf":
        return "application/pdf"
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"

    # Default conservador
    return "application/pdf"
