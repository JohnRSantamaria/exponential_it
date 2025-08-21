import json

from typing import Any
from decimal import Decimal
from fastapi import status
from anthropic import AsyncAnthropic

from app.core.logging import logger
from app.core.settings import settings
from app.services.claude.utils.helpers import _quantize_2, _to_decimal, http_error
from exponential_core.cluadeai import RetentionHTTPResponse


def _build_system_guard() -> str:
    return (
        "You are a precise information extraction engine. "
        "You must output ONLY a single valid JSON object. No preface, no markdown, no comments. "
        "Do not add any text before or after the JSON."
    )


def _build_retention_prompt() -> str:
    return """Lee TODA la factura y DETECTA exclusivamente RETENCIONES (withholdings), p. ej. "Retención", "IRPF", "Retención Fiscal", "Withholding".
No te interesa el IVA ni descuentos comerciales, solo retenciones/withholdings.

REGLAS:
- Busca evidencias de retención explícitas en el documento (líneas como "Retención Fiscal 19% -81,20 €", "IRPF 15%", etc.).
- Si encuentras SOLO el porcentaje, calcula el total usando la base imponible (taxable base, neto antes de IVA).
- Si encuentras SOLO el monto retenido, calcula el porcentaje usando la base imponible.
- Si encuentras ambos (monto y porcentaje), regresa ambos.
- Si NO hay retenciones, has_retention=false y los demás campos en null.
- NO confundas IVA ni descuentos con retención.

DEVUELVE ÚNICAMENTE UN JSON con este esquema (sin texto adicional):
{
  "has_retention": boolean,
  "retention_amount": number | null,  // valor absoluto retenido (positivo)
  "retention_percent": number | null, // % sobre la base imponible (2 decimales)
  "taxable_base": number | null       // base imponible usada para cálculo
}
"""
    # Nota: pedimos taxable_base para poder cerrar cálculos si falta alguno.


async def _call_claude_retention(file_b64: str, media_type: str) -> dict[str, Any]:
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key or api_key.strip() == "":
        http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Claude API key not configured"
        )

    client = AsyncAnthropic(api_key=api_key)

    system = _build_system_guard()
    prompt = _build_retention_prompt()

    # Para PDF usar "document", para imágenes "image" (Anthropic soporta ambas variantes).
    if media_type == "application/pdf":
        content_item = {
            "type": "document",
            "source": {"type": "base64", "media_type": media_type, "data": file_b64},
        }
    else:
        content_item = {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": file_b64},
        }

    messages = [
        {
            "role": "user",
            "content": [content_item, {"type": "text", "text": prompt}],
        }
    ]

    try:
        resp = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0,
            top_p=0.1,
            system=system,
            messages=messages,
        )
    except Exception as e:
        logger.exception("Error calling Claude for retention detection")
        http_error(
            status.HTTP_502_BAD_GATEWAY, "Error calling Claude", {"reason": str(e)}
        )

    # Extrae primer bloque de texto
    text = None
    for block in getattr(resp, "content", []):
        if getattr(block, "type", None) == "text" and hasattr(block, "text"):
            text = block.text
            break

    if not text:
        http_error(status.HTTP_502_BAD_GATEWAY, "Claude response missing text content")

    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Root is not an object")
        return data
    except Exception as e:
        logger.error(
            "Claude returned non-JSON or invalid JSON for retention: %s", text[:500]
        )
        http_error(
            status.HTTP_502_BAD_GATEWAY, "Invalid JSON from Claude", {"reason": str(e)}
        )


def _complete_retention_fields(ai_result: dict[str, Any]) -> RetentionHTTPResponse:
    """
    Cierra los cálculos si falta amount o percent usando taxable_base.
    """
    has_ret = bool(ai_result.get("has_retention", False))

    if not has_ret:
        return RetentionHTTPResponse(
            has_retention=False, total_retention=None, retention_percent=None
        )

    amount = _to_decimal(ai_result.get("retention_amount"))
    percent = _to_decimal(ai_result.get("retention_percent"))
    base = _to_decimal(ai_result.get("taxable_base"))

    # Normaliza amount como absoluto si viene negativo
    if amount is not None and amount < 0:
        amount = abs(amount)

    # Si falta percent y tenemos amount+base => calc
    if percent is None and amount is not None and base and base > 0:
        percent = (amount / base) * Decimal("100")

    # Si falta amount y tenemos percent+base => calc
    if amount is None and percent is not None and base and base > 0:
        amount = (percent / Decimal("100")) * base

    # Redondeos finales a 2 decimales
    amount = _quantize_2(amount) if amount is not None else None
    percent = _quantize_2(percent) if percent is not None else None

    if amount is None and percent is None:
        return RetentionHTTPResponse(
            has_retention=False, total_retention=None, retention_percent=None
        )

    return RetentionHTTPResponse(
        has_retention=True,
        total_retention=amount,
        retention_percent=percent,
    )
