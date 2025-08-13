# app/api/v1/endpoints/invoice_parties.py
import re
import json
from typing import List
from openai import AsyncOpenAI
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from exponential_core.openai import InvoicePartiesSchema
from app.core.settings import settings
from app.services.openai.utils.formatter import (
    pdf_to_data_uris,
    extract_text_with_pymupdf,
)

router = APIRouter()


# ========= Normalizadores/validadores =========
VAT_VALID_REGEX = re.compile(
    r"\b(?:"
    r"[A-HJ-NP-SUVW]\d{7}[0-9A-J]"
    r"|[XYZ]\d{7}[A-Z]"
    r"|\d{8}[TRWAGMYFPDXBNJZSQVHLCKE]"
    r"|[A-Z]{2}[A-Z0-9]{8,12}"
    r")\b",
    re.IGNORECASE,
)


def _norm(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", (s or "")).upper()


# ========= JSON Schema para LLM =========
PARTIES_JSON_SCHEMA = {
    "name": "invoice_parties",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "partner_name": {"type": "string"},
            "partner_tax_it": {"type": "string"},
            "client_name": {"type": "string"},
            "client_tax_it": {"type": "string"},
        },
        "required": ["partner_name", "partner_tax_it", "client_name", "client_tax_it"],
    },
}

PROMPT_PARTIES = (
    "Eres un extractor ESTRICTO de FACTURAS. Devuelve el NOMBRE y el CIF/NIF/VAT "
    "tanto del PROVEEDOR/EMISOR como del CLIENTE/RECEPTOR.\n\n"
    "REGLAS CRÍTICAS:\n"
    "• PROVEEDOR/EMISOR: seller/vendor/issuer (quien emite la factura).\n"
    "• CLIENTE/RECEPTOR: buyer/bill-to/ship-to (quien recibe la factura).\n"
    "• NO uses identificadores de transportistas/logística, bancos, IBAN, pie legal o condiciones.\n"
    "• Normaliza el VAT sin espacios ni guiones; conserva el prefijo de país si está presente.\n"
    "• Responde SOLO en JSON siguiendo el esquema solicitado.\n"
)


async def _call_openai_parties(
    client: AsyncOpenAI, images: List[str], text_hint: str
) -> dict:
    system_msg = "Eres un extractor de datos de facturas y devuelves JSON exacto conforme al esquema solicitado."
    user_text = (
        f"{PROMPT_PARTIES}\n\n"
        "TEXTO EXTRAÍDO (puede contener ruido):\n---\n"
        f"{text_hint[:8000]}\n---\n\n"
        "SALIDA JSON: partner_name, partner_tax_it, client_name, client_tax_it"
    )

    content = [{"type": "text", "text": user_text}]
    for uri in images:
        content.append({"type": "image_url", "image_url": {"url": uri}})

    try:
        resp = await client.chat.completions.create(
            model=getattr(settings, "CHAT_MODEL", settings.MODEL_NAME),
            response_format={"type": "json_schema", "json_schema": PARTIES_JSON_SCHEMA},
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": content},
            ],
            temperature=0,
        )
        return json.loads(resp.choices[0].message.content or "{}")
    except Exception:
        resp = await client.chat.completions.create(
            model=getattr(settings, "CHAT_MODEL", settings.MODEL_NAME),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": content},
            ],
            temperature=0,
        )
        return json.loads(resp.choices[0].message.content or "{}")


def _validate_parties(data: dict) -> InvoicePartiesSchema:
    """
    Validaciones mínimas: campos presentes, VAT válido, sin duplicar proveedor y cliente.
    """
    required_fields = ["partner_name", "partner_tax_it", "client_name", "client_tax_it"]
    for field in required_fields:
        if not data.get(field) or not str(data.get(field)).strip():
            raise HTTPException(
                status_code=422, detail=f"Campo {field} vacío o faltante."
            )

    partner_vat = _norm(data["partner_tax_it"])
    client_vat = _norm(data["client_tax_it"])

    if not VAT_VALID_REGEX.search(partner_vat):
        raise HTTPException(
            status_code=422, detail=f"partner_tax_it inválido: {partner_vat}"
        )
    if not VAT_VALID_REGEX.search(client_vat):
        raise HTTPException(
            status_code=422, detail=f"client_tax_it inválido: {client_vat}"
        )

    if partner_vat == client_vat:
        raise HTTPException(
            status_code=422,
            detail="Proveedor y cliente tienen el mismo VAT, posible error.",
        )

    return InvoicePartiesSchema(**data)


async def extract_invoice_parties(file: UploadFile = File(...)):
    """
    Devuelve proveedor/emisor y cliente/receptor con su nombre y CIF/VAT.
    Selección primaria por OpenAI (imágenes + texto).
    """
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="PDF vacío o no legible.")

    api_key = settings.OPENAI_API_KEY
    if not api_key or not api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key de OpenAI no configurada.",
        )

    client = AsyncOpenAI(api_key=api_key)

    # Rasterizar PDF a imágenes
    try:
        images = pdf_to_data_uris(
            pdf_bytes=pdf_bytes,
            max_pages=getattr(settings, "MAX_PAGES", 3),
            dpi=getattr(settings, "RENDER_DPI", 180),
        )
    except Exception as e:
        raise HTTPException(
            status_code=422, detail=f"No se pudo convertir el PDF a imágenes: {e}"
        )

    # Texto para ayudar al LLM
    try:
        full_text = extract_text_with_pymupdf(pdf_bytes) or ""
    except Exception:
        full_text = ""

    raw = await _call_openai_parties(client, images, full_text)
    return _validate_parties(raw)
