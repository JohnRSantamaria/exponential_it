from typing import List, Optional, Dict
from decimal import Decimal, ROUND_HALF_UP
import re
import base64
import json
import unicodedata

from fastapi import APIRouter, UploadFile, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, ValidationError
from openai import AsyncOpenAI

from app.core.settings import settings
from app.core.logging import logger

# --- PDF -> PNG & texto con PyMuPDF (puro Python, ideal para Alpine) ---
import fitz  # PyMuPDF

router = APIRouter()

# ===================== Modelos estructurados =====================


class Money(BaseModel):
    raw: str = Field(..., description="Texto tal cual aparece (ej: '7.685,38')")
    value: Decimal = Field(
        ..., description="Valor numérico normalizado en punto decimal (ej: 7685.38)"
    )


class InvoiceTotals(BaseModel):
    currency: str = Field(..., description="Moneda detectada, p.ej. 'EUR'")
    subtotal: Money
    tax_amount: Money
    discount_amount: Money
    total: Money
    tax_rate_percent: Decimal = Field(
        ..., description="Porcentaje total de impuestos, p.ej. 21.0"
    )
    # Evidencias: recortes textuales que el modelo vio en el documento
    evidence: Dict[str, List[str]] = Field(
        ..., description="Evidencias por campo (ej: {'total': ['Total 7.685,38']})"
    )
    notes: Optional[str] = None


# ===================== Utilidades =====================

DEC_Q = Decimal("0.01")


def eur_text_to_decimal(s: str) -> Decimal:
    """
    Convierte formatos EU '7.685,38' -> Decimal('7685.38')
    Elimina símbolos no numéricos manteniendo signos y separadores.
    """
    s = s.strip()
    s = re.sub(r"[^\d,.\-]", "", s)
    if "," in s and s.count(",") == 1:
        s = s.replace(".", "").replace(",", ".")
    return Decimal(s)


def almost_equal(a: Decimal, b: Decimal, tol: Decimal = DEC_Q) -> bool:
    return (a - b).copy_abs() <= tol


def normalize_money(m: Money) -> Decimal:
    """
    Preferir parsear desde raw cuando:
      - raw tiene un signo ('-' o '+'), o
      - el valor parseado desde raw es no-cero.
    Si no, usar value.
    """
    parsed_from_raw = None
    if m.raw is not None and str(m.raw).strip():
        try:
            parsed_from_raw = eur_text_to_decimal(str(m.raw))
        except Exception:
            parsed_from_raw = None

    if parsed_from_raw is not None:
        if (
            ("-" in str(m.raw))
            or ("+" in str(m.raw))
            or (parsed_from_raw != Decimal("0"))
        ):
            return parsed_from_raw

    if m.value is not None:
        return Decimal(m.value)

    if parsed_from_raw is not None:
        return parsed_from_raw

    return Decimal("0")


def pdf_to_data_uris(pdf_bytes: bytes, max_pages: int, dpi: int) -> list[str]:
    """
    Renderiza hasta max_pages del PDF a PNG y devuelve data URIs ('data:image/png;base64,...').
    """
    uris: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        n = min(len(doc), max_pages)
        for i in range(n):
            page = doc[i]
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            png_bytes = pix.tobytes("png")
            b64 = base64.b64encode(png_bytes).decode("ascii")
            uris.append(f"data:image/png;base64,{b64}")
    return uris


def extract_text_with_pymupdf(pdf_bytes: bytes) -> str:
    """
    Extrae texto si el PDF es 'digital'. En escaneados (solo imagen), devolverá poco o nada.
    """
    chunks = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            chunks.append(page.get_text("text") or "")
    return "\n".join(chunks).strip()


# --- Matching tolerante para evidencias ---


def _normalize_for_match(s: str) -> str:
    """
    Normaliza texto para matching tolerante:
    - lower
    - quita diacríticos
    - convierte ',' -> '.'
    - elimina separadores y espacios
    - mantiene dígitos, letras, '.', '%'
    - colapsa puntos de miles previos al decimal
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))  # sin acentos
    s = s.lower()
    s = s.replace(",", ".")
    s = re.sub(r"[^a-z0-9.%]+", "", s)
    if s.count(".") >= 2:
        parts = s.split(".")
        suff = ""
        if parts[-1].endswith("%"):
            parts[-1], suff = parts[-1][:-1], "%"
        core = "".join(parts[:-1]) + "." + parts[-1]
        s = core + suff
    return s


def check_evidence_in_text(
    evidence: Dict[str, List[str]], full_text: str
) -> Dict[str, List[str]]:
    """
    Matching tolerante: coma/punto, espacios, %, miles, etc.
    """
    missing: Dict[str, List[str]] = {}
    norm_text = _normalize_for_match(full_text)

    for field, snippets in evidence.items():
        miss_here = []
        for snip in snippets:
            if not snip or not snip.strip():
                continue
            ns = _normalize_for_match(snip)

            ok = False
            if ns:
                if ns in norm_text:
                    ok = True
                else:
                    if ns.endswith("%"):
                        ns2 = ns[:-1]
                        if ns2 in norm_text:
                            ok = True
                    if not ok and re.fullmatch(r"\d+(\.\d+)?%?", ns):
                        base = ns[:-1] if ns.endswith("%") else ns
                        if base in norm_text:
                            ok = True
                        else:
                            trimmed = re.sub(r"\.0+$", "", base)
                            if trimmed and trimmed in norm_text:
                                ok = True

            if not ok:
                miss_here.append(snip)

        if miss_here:
            missing[field] = miss_here

    return missing


# Helpers para política "numbers"
def _is_numeric_snippet(s: str) -> bool:
    return bool(re.search(r"\d", s or ""))


def _any_numeric_snippet_present(snippets: list[str], full_text: str) -> bool:
    norm_text = _normalize_for_match(full_text)
    for snip in snippets or []:
        if _is_numeric_snippet(snip):
            if _normalize_for_match(snip) in norm_text:
                return True
    return False


# Detectar descuentos por línea en el texto
def detect_line_level_discounts(full_text: str) -> list[Decimal]:
    """
    Busca patrones de descuentos por línea, p.ej. 'DTO. 4,00 %', 'Descuento 10%'.
    Devuelve lista de porcentajes como Decimal.
    """
    if not full_text:
        return []
    pat = re.compile(
        r"(?:dto\.?|descuento)\s*[:\-]?\s*(\d{1,3}(?:[.,]\d+)?)\s*%", re.IGNORECASE
    )
    found: list[Decimal] = []
    for m in pat.finditer(full_text):
        pct = m.group(1).replace(",", ".")
        try:
            found.append(Decimal(pct))
        except Exception:
            continue
    return found


# Detectar retenciones (IRPF, Retención Fiscal, etc.)
def detect_withholding(full_text: str) -> Dict[str, Decimal]:
    """
    Detecta retenciones tipo 'Retención Fiscal 19% -81,20 €', 'Retencion IRPF 15 %'.
    Devuelve {'percent': Decimal|None, 'amount': Decimal|None} si detecta algo, o {}.
    """
    if not full_text:
        return {}
    pat = re.compile(
        r"retenci[óo]n(?:\s+fiscal|\s+irpf)?[^%\n\r]*?(\d{1,2}(?:[.,]\d+)?)\s*%([^0-9\-+]*([-+]?[\d.]+(?:[.,]\d{2})))?",
        re.IGNORECASE,
    )
    m = pat.search(full_text)
    if not m:
        return {}
    out: Dict[str, Decimal] = {}
    try:
        out["percent"] = Decimal(m.group(1).replace(",", "."))
    except Exception:
        pass
    amt = m.group(3)
    if amt:
        try:
            out["amount"] = eur_text_to_decimal(amt)
        except Exception:
            pass
    return out


# ===================== OpenAI (Chat Completions con imágenes y JSON) =====================


async def _call_openai_for_invoice_with_images(
    client: AsyncOpenAI,
    user_prompt: str,
    image_data_uris: list[str],
) -> InvoiceTotals:
    """
    Envía 1..N imágenes (data URIs PNG) + prompt. Fuerza salida JSON (json_object).
    """
    sys_msg = (
        "Eres un extractor estricto de facturas. "
        "Responde EXCLUSIVAMENTE en JSON (sin texto adicional) siguiendo el esquema solicitado."
    )

    content: list[dict] = [{"type": "text", "text": user_prompt}]
    for uri in image_data_uris:
        content.append({"type": "image_url", "image_url": {"url": uri}})

    chat = await client.chat.completions.create(
        model=getattr(settings, "CHAT_MODEL", settings.MODEL_NAME),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": content},
        ],
        temperature=0,
    )

    json_text = chat.choices[0].message.content
    if not json_text or not json_text.strip():
        raise HTTPException(
            status_code=502, detail="No se recibió contenido JSON del modelo."
        )
    try:
        return InvoiceTotals.model_validate_json(json_text)
    except ValidationError as ve:
        logger.error(f"JSON recibido no valida contra InvoiceTotals: {json_text}")
        raise ve


# ===================== Servicio principal =====================


async def extract_data_from_invoice(file: UploadFile) -> InvoiceTotals:
    file_bytes = await file.read()

    api_key = settings.OPENAI_API_KEY
    if not api_key or not api_key.strip():
        logger.error("🔒 OPENAI_API_KEY no está definida o está vacía.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key de OpenAI no configurada correctamente.",
        )
    logger.info("✅ API Key de OpenAI detectada.")

    client = AsyncOpenAI(api_key=api_key)

    # 1) Renderizar PDF a imágenes (1..N páginas según settings)
    try:
        data_uris = pdf_to_data_uris(
            pdf_bytes=file_bytes,
            max_pages=settings.MAX_PAGES,
            dpi=settings.RENDER_DPI,
        )
        if not data_uris:
            raise ValueError("No fue posible rasterizar el PDF a imágenes.")
    except Exception as e:
        logger.exception("Error convirtiendo PDF a imágenes")
        raise HTTPException(
            status_code=422, detail=f"No se pudo convertir el PDF a imágenes: {e}"
        )

    # 2) Prompt multimodal
    prompt = (
        "Extrae SOLO lo que ves en la factura (imágenes). Devuelve JSON con:\n"
        "- currency (ej: 'EUR')\n"
        "- subtotal {raw, value}\n"
        "- tax_amount {raw, value}\n"
        "- discount_amount {raw, value}\n"
        "- total {raw, value}\n"
        "- tax_rate_percent (porcentaje total de impuestos)\n"
        "- evidence: para cada campo, arrays de cadenas EXACTAS visibles en la imagen (p.ej. 'IVA (21,00%)').\n\n"
        "Reglas:\n"
        "1) El % de impuestos debe coincidir con lo visible (p.ej. 'IVA (21,00%)').\n"
        "2) Si hay varios impuestos/ajustes, resume el % total que afecta al total mostrado.\n"
        "3) Si no hay descuentos visibles, discount_amount = 0.\n"
        "4) 'raw' debe ser exactamente como se ve (coma/punto, símbolo, separadores).\n"
        "5) 'value' debe ser numérico con punto decimal.\n"
        "6) Prioriza la tabla/pie de totales si hay conflicto.\n"
    )

    # 3) Llamada al modelo (imágenes + JSON mode)
    try:
        parsed: InvoiceTotals = await _call_openai_for_invoice_with_images(
            client=client,
            user_prompt=prompt,
            image_data_uris=data_uris,
        )
    except ValidationError as ve:
        logger.exception("El modelo no devolvió el esquema esperado.")
        raise HTTPException(status_code=502, detail=f"Respuesta no estructurada: {ve}")
    except Exception as e:
        logger.exception("Error llamando a OpenAI.")
        raise HTTPException(status_code=500, detail=f"Error procesando con OpenAI: {e}")

    # 4) Validaciones locales

    # 4a) Texto embebido (si lo hay) y detectores
    full_text = ""
    try:
        full_text = extract_text_with_pymupdf(file_bytes)
    except Exception:
        full_text = ""

    line_discounts = detect_line_level_discounts(full_text)
    withholding = detect_withholding(full_text)
    is_withholding = bool(withholding)

    # Evidencias segun política
    missing_evidence: Dict[str, List[str]] = {}
    if full_text and settings.EVIDENCE_POLICY != "off":
        missing_evidence = check_evidence_in_text(parsed.evidence, full_text)

        if settings.EVIDENCE_POLICY == "numbers":
            if "tax_rate_percent" in missing_evidence:
                del missing_evidence["tax_rate_percent"]
            for fld in ["subtotal", "tax_amount", "total"]:
                if fld in missing_evidence:
                    if _any_numeric_snippet_present(
                        parsed.evidence.get(fld, []), full_text
                    ):
                        del missing_evidence[fld]

    # 4b) Aritmética y % impuestos
    sub = normalize_money(parsed.subtotal)
    tax = normalize_money(parsed.tax_amount)
    disc = normalize_money(parsed.discount_amount)
    ttl = normalize_money(parsed.total)

    # --- RECONCILIACIÓN DE DESCUENTO / RETENCIÓN (robusta) ---
    computed_total_no_disc = (sub + tax).quantize(DEC_Q, rounding=ROUND_HALF_UP)
    computed_total_with_disc = (sub - disc + tax).quantize(
        DEC_Q, rounding=ROUND_HALF_UP
    )

    if almost_equal(ttl, computed_total_no_disc):
        disc_effective = Decimal("0")
    elif almost_equal(ttl, computed_total_with_disc):
        disc_effective = disc
    else:
        # Infiera "descuento/retención" desde totales si hace cuadrar
        inferred = (sub + tax - ttl).quantize(DEC_Q, rounding=ROUND_HALF_UP)
        if inferred >= Decimal("0") and almost_equal(
            ttl, (sub - inferred + tax).quantize(DEC_Q, rounding=ROUND_HALF_UP)
        ):
            disc_effective = inferred
            label = "Retención inferida" if is_withholding else "Descuento inferido"
            note = f"{label} a partir de totales: {inferred}"
            parsed.notes = (parsed.notes + " | " + note) if parsed.notes else note
        else:
            disc_effective = disc  # quedará mismatch

    computed_total = (sub - disc_effective + tax).quantize(
        DEC_Q, rounding=ROUND_HALF_UP
    )
    math_ok = almost_equal(ttl, computed_total)

    # --- Tasa de IVA: si hay retención, NO reduce la base ---
    if is_withholding:
        base_for_vat = sub
    else:
        base_for_vat = max(Decimal("0"), (sub - disc_effective))

    computed_rate = (
        ((tax / base_for_vat) * Decimal("100")).quantize(Decimal("0.01"))
        if base_for_vat > 0
        else Decimal("0")
    )
    rate_ok = almost_equal(parsed.tax_rate_percent, computed_rate, Decimal("0.1"))

    problems = []
    warnings = []

    # Evidencias: solo rompen en modo strict
    if full_text and settings.EVIDENCE_POLICY == "strict" and missing_evidence:
        problems.append({"type": "evidence_missing", "details": missing_evidence})
    elif full_text and settings.EVIDENCE_POLICY == "numbers" and missing_evidence:
        warnings.append({"type": "evidence_missing", "details": missing_evidence})

    if not math_ok:
        problems.append(
            {
                "type": "math_mismatch",
                "expected_total": str(computed_total),
                "reported_total": str(ttl),
            }
        )
    if not rate_ok:
        problems.append(
            {
                "type": "tax_rate_mismatch",
                "expected_rate_percent": str(computed_rate),
                "reported_rate_percent": str(parsed.tax_rate_percent),
            }
        )

    # Notas informativas
    if line_discounts:
        msg = f"Descuentos por línea detectados: [{', '.join(f'{d:.2f}%' for d in line_discounts)}]"
        if disc_effective == 0 and disc > 0:
            msg += ". El descuento informado no afecta a los totales."
        elif disc_effective == 0 and disc == 0:
            msg += ". No afectan al total final."
        parsed.notes = (parsed.notes + " | " + msg) if parsed.notes else msg

    if is_withholding:
        msg = "Retención detectada"
        if "percent" in withholding:
            msg += f" {withholding['percent']}%"
        if "amount" in withholding:
            msg += f" por {withholding['amount']}"
        # Si no hay amount en texto, estimar desde totales
        inferred_w = (sub + tax - ttl).quantize(DEC_Q, rounding=ROUND_HALF_UP)
        if "amount" not in withholding and inferred_w:
            msg += f". Importe inferido: {inferred_w}"
        parsed.notes = (parsed.notes + " | " + msg) if parsed.notes else msg

    if problems:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(
                {
                    "message": "La extracción no pasa las validaciones.",
                    "problems": problems,
                    "warnings": warnings or None,
                    "extracted": parsed.model_dump(mode="json"),
                }
            ),
        )

    if warnings:
        note = f"Warnings: {json.dumps(warnings, ensure_ascii=False)}"
        parsed.notes = (parsed.notes + " | " + note) if parsed.notes else note

    return parsed
