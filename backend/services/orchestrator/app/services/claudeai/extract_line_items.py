import json

from typing import List, Any, Tuple
from fastapi import UploadFile
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, ValidationError

from app.core.logging import logger
from app.services.claudeai.client import ClaudeAIService
from app.services.taggun.exceptions import AdminServiceError, FileProcessingError
from app.services.taggun.schemas.taggun_models import LineItemSchema
from exponential_core.cluadeai import InvoiceResponseSchema

from app.services.taggun.utils.conversion_to_decimal import D, f2, quant2


def _to_decimal(value) -> Decimal:
    """Convertir cualquier valor (str, float, Decimal) a Decimal de forma segura."""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _truncate(obj: Any, max_len: int = 2000) -> Any:
    """
    Evita loggear payloads gigantes: si es str lo recorta; si es dict,
    devuelve una versión JSON recortada.
    """
    try:
        s = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False)
    except Exception:
        s = repr(obj)
    return s[:max_len] + ("…<truncated>" if len(s) > max_len else "")


async def extract_claude_invoice_data(
    file: UploadFile,
    file_content: bytes,
    claudeai_service: ClaudeAIService,
) -> InvoiceResponseSchema:
    logger.info("Comienza el proceso de obtención de ítems a través de Claude AI.")

    try:
        response = await claudeai_service.extract_claude_invoce(
            file=file, file_content=file_content
        )
    except Exception as exc:
        # Errores de red / tiempo / etc. del cliente
        raise AdminServiceError(
            message="Error al comunicarse con el servicio Claude",
            data={"error": str(exc)},
        )

    # Normaliza a dict
    try:
        if isinstance(response, BaseModel):
            payload = response.model_dump()  # ✅ dict
        elif isinstance(response, dict):
            payload = response
        elif isinstance(response, str):
            payload = json.loads(response)  # ✅ parsea JSON string → dict
        elif hasattr(response, "json") and callable(getattr(response, "json")):
            payload = response.json()  # httpx.Response o similar
        else:
            raise AdminServiceError(
                message="Tipo de respuesta no soportado desde Claude",
                data={"type": type(response).__name__},
            )
    except Exception as exc:
        raise FileProcessingError(
            message="No se pudo parsear la respuesta de Claude",
            data={"error": str(exc), "response_preview": _truncate(response)},
        )

    # Valida con Pydantic v2
    try:
        # Recomendado en v2 en lugar de **payload
        return InvoiceResponseSchema.model_validate(payload)
        # (alternativa equivalente si prefieres kwargs y estás seguro de que es dict:)
        # return InvoiceResponseSchema(**payload)
    except ValidationError as ve:
        # Log útil y error claro hacia arriba
        logger.error(
            "❌ Error al validar JSON contra InvoiceResponseSchema: %s",
            _truncate(payload),
        )
        raise FileProcessingError(
            message="La respuesta de Claude no valida contra el esquema esperado",
            data={"errors": ve.errors(), "payload_preview": _truncate(payload)},
        )


async def line_items_extraction(
    invoice_data: InvoiceResponseSchema,
) -> Tuple[List[LineItemSchema], Decimal]:
    """
    Extrae ítems ya normalizados (usando D/f2) y devuelve también
    la suma total de líneas como Decimal (cuantizada a 2 decimales).
    """
    parsed_items: List[LineItemSchema] = []
    items = invoice_data.items or []

    lines_total: Decimal = Decimal("0.00")

    for item in items:
        # Normaliza cantidad y precio unitario desde el schema de la IA
        qty_dec = D(getattr(item, "quantity", 0), default="0")
        unit_price_dec = D(getattr(item, "unit_price", 0), default="0")

        # Usa line_total si viene; si no, calcula unit_price * quantity
        lt_from_schema = getattr(item, "line_total", None)
        line_total_dec = D(lt_from_schema, default="0")
        if line_total_dec == Decimal("0") and (unit_price_dec != 0 and qty_dec != 0):
            line_total_dec = unit_price_dec * qty_dec

        lines_total += line_total_dec

        parsed_items.append(
            LineItemSchema(
                name=(getattr(item, "description", "") or "").strip(),
                quantity=float(qty_dec),  # en tu schema quantity es float
                unit_price=f2(unit_price_dec),  # float con 2 decimales
                total_price=f2(line_total_dec),  # float con 2 decimales
            )
        )

    # Devuelve el total cuantizado a 2 decimales para coherencia financiera
    return parsed_items, quant2(lines_total)
