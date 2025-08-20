from __future__ import annotations

import base64
import json
from decimal import Decimal
from typing import Dict, Any, Optional, List

from fastapi import UploadFile
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.settings import settings
from app.core.logging import logger
from exponential_core.exceptions import CustomAppException
from anthropic import AsyncAnthropic

from app.services.claude.exceptions import (
    APIKeyNotConfiguredException,
    AnthropicAPIException,
    FileProcessingException,
    InvalidInvoiceException,
    JSONParsingException,
    UnsupportedFileFormatException,
)

# ============================================================
#                      Pydantic v2 Models
# ============================================================


class Company(BaseModel):
    name: str
    address: str
    tax_id: str
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None


class Customer(BaseModel):
    name: str
    tax_number: str
    address: str


class GeneralInfo(BaseModel):
    company: Company
    customer: Customer
    invoice_date: str  # e.g. "13/06/2025"
    invoice_number: str
    project: Optional[str] = None
    manager: Optional[str] = None
    delivery_note: Optional[str] = None
    order_number: Optional[str] = None
    notes: Optional[str] = None


def _to_decimal(value):
    """
    Coerce int/float/str -> Decimal safely.
    - Floats are wrapped via str() to avoid binary artifacts.
    - Strings like '7,50' are normalized to '7.50'.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        v = value.strip().replace(",", ".")
        return Decimal(v)
    return value


class Item(BaseModel):
    # Optional metadata
    date: Optional[str] = None
    delivery_code: Optional[str] = None
    product_code: Optional[str] = None

    description: str
    # CHANGED: quantity can be fractional (e.g., cubic meters), so use Decimal
    quantity: Decimal
    # CHANGED: unit can be missing => Optional[str]
    unit: Optional[str] = None

    unit_price: Decimal
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    net_price: Decimal
    line_total: Decimal

    measurements: Optional[str] = None
    color: Optional[str] = None
    weight_kg: Optional[Decimal] = None
    notes: Optional[str] = None

    # Normalize numeric fields to Decimal
    @field_validator(
        "quantity",
        "unit_price",
        "discount_percent",
        "discount_amount",
        "net_price",
        "line_total",
        "weight_kg",
        mode="before",
    )
    @classmethod
    def _normalize_decimals(cls, v):
        return _to_decimal(v)


class Totals(BaseModel):
    subtotal: Optional[Decimal] = None
    taxable_base: Decimal
    vat_percent: Decimal
    vat_amount: Decimal
    other_taxes: Optional[Decimal] = None
    grand_total: Decimal

    @field_validator(
        "subtotal",
        "taxable_base",
        "vat_percent",
        "vat_amount",
        "other_taxes",
        "grand_total",
        mode="before",
    )
    @classmethod
    def _normalize_decimals(cls, v):
        return _to_decimal(v)


class PaymentMethod(BaseModel):
    method: str
    due_date: str
    iban: Optional[str] = None
    terms: Optional[str] = None


class InvoiceResponse(BaseModel):
    # Estructura que esperamos de Claude (en inglés)
    general_info: GeneralInfo
    items: List[Item]
    totals: Totals
    payment: PaymentMethod


# ============================================================
#                        Prompt (English)
# ============================================================


def create_extraction_prompt() -> str:
    """
    Create the prompt to extract invoice data (multi-page PDF or image).
    """
    return """Analyze this COMPLETE invoice (PDF or image) and extract ALL structured information in valid JSON format.

CRITICAL: You must extract EVERY SINGLE LINE ITEM without exception. DO NOT summarize, DO NOT group, DO NOT omit any line.

MANDATORY INSTRUCTIONS:
1. If it's a PDF: Analyze ALL pages of the document.
2. Extract EVERY line item one by one, even if repetitive or similar.
3. Each row in the item table must be a separate object inside the "items" array.
4. DO NOT group similar items — every line must appear individually.
5. If there are 30+ items, you MUST include ALL 30+ items in the JSON.
6. Process ALL pages of the document.
7. For images: Analyze the entire image completely.

IMPORTANT: You must return ONLY a valid JSON object — no extra text, no code markers, no explanations.

The structure must follow exactly this schema:

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
      "quantity": number,              // quantity CAN be fractional (e.g., 7.5)
      "unit": "string or null",        // unit may be missing; use null
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

EXAMPLE OF COMPLETE EXTRAXTION FROM MULTI-PAGE PDF:
If there is a table continuing across multiple pages with these rows:

PAGE 1:
- 29-07-2025 61076393 Pumpable 7.50 M3 2.50 18.75
- 29-07-2025 61076393 Special Solera 7.50 M3 2.00 15.00
- 29-07-2025 61076393 HA-25-BLANDA 7.50 M3 74.00 555.00
- [... continues ...]

PAGE 2:
- 29-07-2025 61076395 Pumpable 7.50 M3 2.50 18.75
- 29-07-2025 61076395 Special Solera 7.50 M3 2.00 15.00
- [... rest of lines ...]

You must create a separate object in "items" for EVERY line from ALL pages.

Important rules:
1. If a field doesn't exist, use null.
2. Numbers must be numbers, not strings.
3. Dates should remain strings in the original format.
4. For discounts: if there is a "% Dto." column, extract both discount_percent and discount_amount.
5. net_price = unit_price - discount_amount (if applicable).
6. line_total = net_price * quantity.
7. Extract ABSOLUTELY ALL line items from ALL pages — if you omit any, the result is invalid.
8. DO NOT add explanations or text, ONLY return the JSON.

FINAL CHECK: Before sending your answer, count how many objects exist in the "items" array and make sure it matches the total number of rows across ALL pages of the invoice.

Respond only with the COMPLETE valid JSON:"""


# ============================================================
#                 Helper: clean & validate JSON
# ============================================================


def _clean_possible_markdown(json_text: str) -> str:
    """
    Removes ```json ... ``` wrappers if present and trims whitespace.
    """
    clean = json_text.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    if clean.startswith("```"):  # in case of ``` without language
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    return clean.strip()


def parse_invoice_response_from_json(json_text: str) -> InvoiceResponse:
    """
    Validates the JSON returned by Claude and converts it to English models.
    """
    clean = _clean_possible_markdown(json_text)
    try:
        return InvoiceResponse.model_validate_json(clean)
    except ValidationError as ve:
        raise ve


# ============================================================
#                    Core processing function
# ============================================================


async def invoice_formater(file: UploadFile) -> Dict[str, Any]:
    """
    Procesa un archivo único (PDF o imagen) de factura y devuelve datos estructurados en JSON
    (claves en inglés).
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

        # Crear el prompt para Claude (en inglés)
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
        else:  # Es una imagen
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
                messages=messages,
            )
        except Exception as e:
            raise AnthropicAPIException(str(e), file.filename)

        # Extraer el texto de la respuesta
        response_text = response.content[0].text
        logger.info(f"✅ Respuesta recibida para {file.filename}")

        # Parsear y validar con Pydantic
        try:
            validated: InvoiceResponse = parse_invoice_response_from_json(response_text)
            items_count = len(validated.items)
            logger.info(f"✅ {file.filename}: Se extrajeron {items_count} ítems")

            # Si necesitaras convertir Decimal -> float para respuesta JSON final:
            # invoice_dict = json.loads(json.dumps(validated.model_dump(), default=float))

            invoice_dict = validated.model_dump()  # conserva Decimal

            return {
                "success": True,
                "filename": file.filename,
                "file_type": media_type,
                "items_extracted": items_count,
                "invoice_data": invoice_dict,  # claves en inglés
            }

        except ValidationError as e:
            logger.error(f"❌ Error al validar JSON de {file.filename}: {str(e)}")
            logger.error(f"Respuesta recibida: {response_text[:500]}...")
            raise JSONParsingException(file.filename, str(e))

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


# ============================================================
#                 File utils (format & media type)
# ============================================================


def is_supported_file_format(filename: str) -> bool:
    """
    Verifica si el formato de archivo es soportado
    """
    supported_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
    filename_lower = filename.lower()
    return any(filename_lower.endswith(ext) for ext in supported_extensions)


def get_media_type(filename: str) -> str:
    """
    Determina el media type basado en la extensión del archivo
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        return "application/pdf"
    elif filename_lower.endswith(".jpg") or filename_lower.endswith(".jpeg"):
        return "image/jpeg"
    elif filename_lower.endswith(".png"):
        return "image/png"
    elif filename_lower.endswith(".webp"):
        return "image/webp"
    else:
        return "application/octet-stream"
