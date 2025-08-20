from __future__ import annotations

import base64
import json

from fastapi import UploadFile
from pydantic import ValidationError

from app.core.settings import settings
from app.core.logging import logger
from anthropic import AsyncAnthropic

from exponential_core.cluadeai import InvoiceResponseSchema
from app.services.claude.exceptions import (
    APIKeyNotConfiguredException,
    AnthropicAPIException,
    FileProcessingException,
    InvalidInvoiceException,
    JSONParsingException,
    UnsupportedFileFormatException,
)
from app.services.claude.utils.cleaner import parse_invoice_response_from_json
from app.services.claude.utils.format_response import (
    get_media_type,
    is_supported_file_format,
)

# ---------- Prompts ----------


def create_system_guard() -> str:
    # Refuerza que SOLO debe responder con un JSON válido.
    return (
        "You are a strict information extraction engine. "
        "Output MUST be a single JSON object (no preface, no markdown, no comments). "
        "Do not include any text before or after the JSON."
    )


def create_extraction_prompt() -> str:
    return """Analyze this COMPLETE invoice (PDF or image) and extract ALL structured information in valid JSON.

CRITICAL:
- Return ONLY a valid JSON object (no extra text).
- Process ALL pages.
- Extract EVERY line item (no grouping, no skipping).
- Numbers MUST be numbers (not strings).
- For the following fields, NEVER return null; if not present in the document, use the literal string "N/A":
  general_info.company.address, general_info.company.tax_id,
  general_info.customer.address,
  payment.method, payment.due_date

Schema:
{
  "general_info": {
    "company": {
      "name": "string",
      "address": "string",
      "tax_id": "string",
      "phone": "string or null",
      "fax": "string or null",
      "email": "string or null"
    },
    "customer": {
      "name": "string",
      "tax_number": "string",
      "address": "string"
    },
    "invoice_date": "string",
    "invoice_number": "string",
    "project": "string or null",
    "manager": "string or null",
    "delivery_note": "string or null",
    "order_number": "string or null",
    "notes": "string or null"
  },
  "items": [
    {
      "date": "string or null",
      "delivery_code": "string or null",
      "product_code": "string or null",
      "description": "string",
      "quantity": number,
      "unit": "string or null",
      "unit_price": number,
      "discount_percent": number or null,
      "discount_amount": number or null,
      "net_price": number,
      "line_total": number,
      "measurements": "string or null",
      "color": "string or null",
      "weight_kg": number or null,
      "notes": "string or null"
    }
  ],
  "totals": {
    "subtotal": number or null,
    "taxable_base": number,
    "vat_percent": number,
    "vat_amount": number,
    "other_taxes": number or null,
    "grand_total": number
  },
  "payment": {
    "method": "string",
    "due_date": "string",
    "iban": "string or null",
    "terms": "string or null"
  }
}

Rules:
1) If a numeric field is missing, infer if possible; otherwise return 0.0 for optional numeric fields.
2) ABSOLUTELY include every line item across ALL pages; if 30+ rows, include all 30+.
3) Dates remain strings as-is.
4) Do NOT output any explanation, ONLY the JSON.

FINAL CHECK before sending:
- Ensure the fields listed above are "N/A" instead of null when absent.
- Ensure numeric fields are numbers (not strings).
- Ensure items array has ALL lines from the tables, no omissions.

Respond with the JSON only:
"""


# ---------- Utilidades de parsing/normalización ----------

_NON_NULL_STR_FIELDS = {
    ("general_info", "company", "address"),
    ("general_info", "company", "tax_id"),
    ("general_info", "customer", "address"),
    ("payment", "method"),
    ("payment", "due_date"),
}

_NUMERIC_FIELDS = {
    ("totals", "taxable_base"),
    ("totals", "vat_percent"),
    ("totals", "vat_amount"),
    ("totals", "grand_total"),
}


def _set_path(obj, path, value):
    ref = obj
    for k in path[:-1]:
        if isinstance(ref, dict) and k in ref:
            ref = ref[k]
        else:
            return
    if isinstance(ref, dict):
        ref[path[-1]] = value


def _get_path(obj, path):
    ref = obj
    for k in path:
        if not isinstance(ref, dict) or k not in ref:
            return None
        ref = ref[k]
    return ref


def _to_number(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return v
    try:
        # quita separadores si vinieran
        return float(str(v).replace(",", "").strip())
    except Exception:
        return None


def repair_and_normalize_json(text: str, filename: str) -> str:
    data = json.loads(text)
    # Validar items presente y no vacío
    items = data.get("items", None)
    if not isinstance(items, list) or len(items) == 0:
        reason = "La respuesta no contiene ítems extraídos (items vacío o ausente)."
        logger.error("❌ %s | %s", filename, reason)
        raise InvalidInvoiceException(filename, reason)

    # Forzar "N/A" en strings que no deben ser null
    for path in _NON_NULL_STR_FIELDS:
        val = _get_path(data, path)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            _set_path(data, path, "N/A")

    # Convertir numéricos
    for path in _NUMERIC_FIELDS:
        val = _get_path(data, path)
        num = _to_number(val)
        _set_path(data, path, num)

    return json.dumps(data, ensure_ascii=False)


def format_pydantic_errors(e: ValidationError) -> str:
    parts = []
    for err in e.errors():
        loc = "/".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "")
        got = err.get("input", None)
        parts.append(f"- {loc}: {msg}. input={got!r}")
    return "\n".join(parts)


def extract_first_text_block(resp) -> str:
    # Anthropic puede devolver varios bloques; tomamos el primero de tipo texto.
    for block in getattr(resp, "content", []):
        if getattr(block, "type", None) == "text" and hasattr(block, "text"):
            return block.text
    raise AnthropicAPIException(
        "La respuesta no contiene un bloque de texto utilizable.", "<internal>"
    )


# ---------- Handler principal ----------


async def invoice_formater(file: UploadFile) -> InvoiceResponseSchema:
    """
    Procesa un archivo único (PDF o imagen) de factura y devuelve datos estructurados
    """
    api_key = settings.ANTHROPIC_API_KEY

    if not api_key or api_key.strip() == "":
        logger.error("🔒 ClaudeAI_API_KEY no está definida o está vacía.")
        raise APIKeyNotConfiguredException()
    else:
        logger.info("✅ API Key de ClaudeAI detectada.")

    client = AsyncAnthropic(api_key=api_key)

    try:
        logger.info(f"📄 Procesando archivo: {file.filename}")

        # Validar formato de archivo
        if not is_supported_file_format(file.filename):
            raise UnsupportedFileFormatException(file.filename)

        # Leer el contenido del archivo
        try:
            file_content = await file.read()
        except Exception as e:
            raise FileProcessingException(file.filename, "reading", str(e))

        # Convertir a base64
        try:
            base64_content = base64.b64encode(file_content).decode("utf-8")
        except Exception as e:
            raise FileProcessingException(file.filename, "base64_encoding", str(e))

        # Determinar el media type basado en la extensión
        try:
            media_type = get_media_type(file.filename)
        except Exception as e:
            raise FileProcessingException(file.filename, "media_type_detection", str(e))

        # Prompts
        system = create_system_guard()
        prompt = create_extraction_prompt()

        # Crear el mensaje con el archivo (PDF o imagen)
        if media_type == "application/pdf":
            content_item = {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_content,
                },
            }
        else:
            content_item = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_content,
                },
            }

        messages = [
            {
                "role": "user",
                "content": [
                    content_item,
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        logger.info(f"🤖 Enviando {file.filename} a Claude para procesamiento...")

        # Llamar a la API de Claude
        try:
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8192,
                temperature=0,
                top_p=0.1,  # más seguro que 0 estricto
                system=system,
                messages=messages,
            )
        except Exception as e:
            raise AnthropicAPIException(str(e), file.filename)

        # Extraer el texto de la respuesta
        response_text = extract_first_text_block(response)
        logger.info(f"✅ Respuesta recibida para {file.filename}")

        # Normalizar y validar con Pydantic
        try:
            normalized_json = repair_and_normalize_json(response_text, file.filename)
            validated: InvoiceResponseSchema = parse_invoice_response_from_json(
                normalized_json
            )
            items_count = len(validated.items)
            logger.info(f"✅ {file.filename}: Se extrajeron {items_count} ítems")
            return validated

        except ValidationError as e:
            formatted = format_pydantic_errors(e)
            logger.error(
                "❌ Error al validar JSON de %s:\n%s\n---\nRespuesta (primeros 1000 chars): %s",
                file.filename,
                formatted,
                response_text[:1000],
            )
            raise JSONParsingException(file.filename, formatted)

    except (
        APIKeyNotConfiguredException,
        UnsupportedFileFormatException,
        FileProcessingException,
        AnthropicAPIException,
        JSONParsingException,
        InvalidInvoiceException,
    ):
        # Re-lanzar excepciones específicas
        raise
    except Exception as e:
        logger.error(f"❌ Error durante el procesamiento de {file.filename}: {str(e)}")
        raise FileProcessingException(file.filename, "unexpected_error", str(e))
