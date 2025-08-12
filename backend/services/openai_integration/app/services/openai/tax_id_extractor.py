# app/api/v1/endpoints/invoice_partner.py
import re
import json

from typing import Optional
from openai import AsyncOpenAI
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from exponential_core.openai import PartnerTaxIdSchema

from app.core.logging import logger
from app.core.settings import settings
from app.services.openai.utils.formatter import (
    pdf_to_data_uris,
    extract_text_with_pymupdf,
)
from app.services.openai.utils.tax_id_extractor import (
    PARTNER_JSON_SCHEMA,
    PROMPT_VENDOR,
    VAT_REGEX,
)

router = APIRouter()


def _normalize_vat(v: Optional[str]) -> str:
    if not v:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", v).upper()


async def _call_openai_for_partner_with_images(
    client: AsyncOpenAI,
    prompt: str,
    image_data_uris: list[str],
    client_tax_excluded: str,
    extracted_text_hint: str,
) -> dict:
    """
    Llama al modelo con imágenes (y pista de texto) y fuerza JSON Schema.
    Incluye el CIF del cliente a excluir dentro del mensaje de usuario.
    """
    system_msg = "Eres un extractor de datos de facturas y debes devolver JSON exacto conforme al esquema."

    # Contenido multimodal: prompt + texto extraído + CIF del cliente a excluir + imágenes
    user_text = (
        f"{prompt}\n\n"
        f"EXCLUIR explícitamente este CIF/NIF (cliente): '{client_tax_excluded}'\n\n"
        "TEXTO EXTRAÍDO (pista, puede contener ruido):\n---\n"
        f"{extracted_text_hint}\n---\n\n"
        "SALIDA JSON con: partner_name, partner_tax_it"
    )
    content = [{"type": "text", "text": user_text}]
    for uri in image_data_uris:
        content.append({"type": "image_url", "image_url": {"url": uri}})

    # 1) Intento con json_schema
    try:
        chat = await client.chat.completions.create(
            model=getattr(settings, "CHAT_MODEL", settings.MODEL_NAME),
            response_format={"type": "json_schema", "json_schema": PARTNER_JSON_SCHEMA},
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": content},
            ],
            temperature=0,
        )
        json_text = chat.choices[0].message.content
        return json.loads(json_text)
    except Exception:
        # 2) Fallback a json_object
        chat = await client.chat.completions.create(
            model=getattr(settings, "CHAT_MODEL", settings.MODEL_NAME),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": content},
            ],
            temperature=0,
        )
        json_text = chat.choices[0].message.content
        return json.loads(json_text)


def _post_validate_partner(data: dict, client_tax_excluded: str) -> PartnerTaxIdSchema:
    """
    Validación defensiva local:
    - Campos presentes
    - Normalización/regex VAT
    - Exclusión del VAT del cliente
    """
    name = (data.get("partner_name") or "").strip()
    vat = _normalize_vat(data.get("partner_tax_it"))

    if not name or not vat:
        raise HTTPException(
            status_code=422,
            detail="No fue posible identificar proveedor y VAT de forma inequívoca.",
        )

    excluded = _normalize_vat(client_tax_excluded)
    if excluded and vat == excluded:
        raise HTTPException(
            status_code=422,
            detail="El modelo devolvió el CIF/NIF del cliente, no el del proveedor.",
        )

    if not VAT_REGEX.search(vat):
        raise HTTPException(
            status_code=422,
            detail=f"El valor extraído no parece un CIF/NIF/VAT válido: {vat}",
        )

    return PartnerTaxIdSchema(partner_name=name, partner_tax_it=vat)


async def extract_partner_taxid(
    client_tax_id: Optional[str],
    file: UploadFile = File(...),
) -> PartnerTaxIdSchema:
    """
    Devuelve el nombre legal y el CIF/NIF/VAT del PROVEEDOR/EMISOR.
    - Usa el mismo flujo que /extract-invoice: rasteriza PDF a PNGs y llama al modelo en JSON mode.
    - Excluye explícitamente el CIF/NIF del cliente que envías.
    - Aplica validaciones locales y regex para evitar terceros (transportes/IBAN).
    """
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="PDF vacío o no legible.")

    api_key = settings.OPENAI_API_KEY
    if not api_key or not api_key.strip():
        logger.error("🔒 OPENAI_API_KEY no está definida o está vacía.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key de OpenAI no configurada correctamente.",
        )
    client = AsyncOpenAI(api_key=api_key)
    logger.info("✅ API Key de OpenAI detectada, comienza Extración del partner taxid")

    # 1) Render -> imágenes (como /extract-invoice)
    try:
        data_uris = pdf_to_data_uris(
            pdf_bytes=pdf_bytes,
            max_pages=getattr(settings, "MAX_PAGES", 3),
            dpi=getattr(settings, "RENDER_DPI", 180),
        )
        if not data_uris:
            raise ValueError("No fue posible rasterizar el PDF a imágenes.")
    except Exception as e:
        logger.exception("Error convirtiendo PDF a imágenes")
        raise HTTPException(
            status_code=422, detail=f"No se pudo convertir el PDF a imágenes: {e}"
        )

    # 2) Extraer texto 'hint' (opcional, ayuda al LLM a desambiguar)
    try:
        full_text = extract_text_with_pymupdf(pdf_bytes)
    except Exception:
        full_text = ""

    # 3) Llamada a OpenAI (multimodal + json schema) con exclusión del cliente
    try:
        raw = await _call_openai_for_partner_with_images(
            client=client,
            prompt=PROMPT_VENDOR,
            image_data_uris=data_uris,
            client_tax_excluded=_normalize_vat(client_tax_id),
            extracted_text_hint=full_text[:8000],  # límite prudente
        )
    except Exception as e:
        logger.exception("Error llamando a OpenAI para partner.")
        raise HTTPException(status_code=500, detail=f"Error procesando con OpenAI: {e}")

    # 4) Post-validación defensiva
    return _post_validate_partner(raw, client_tax_id or "")
