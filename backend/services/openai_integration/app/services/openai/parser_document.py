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
        ..., description="Porcentaje total de IVA, p.ej. 21.0"
    )
    # NUEVO: Retención (IRPF, retención fiscal, etc.)
    withholding_amount: Money = Field(
        default_factory=lambda: Money(raw="0", value=Decimal("0")),
        description="Retención aplicada al pago (no reduce base de IVA)",
    )
    withholding_rate_percent: Decimal = Field(
        default=Decimal("0"), description="Porcentaje de retención, p.ej. 19.0"
    )
    # Evidencias: recortes textuales que el modelo vio en el documento
    evidence: Dict[str, List[str]] = Field(
        ..., description="Evidencias por campo (ej: {'total': ['Total 7.685,38']})"
    )
    notes: Optional[str] = None


# ===================== Utilidades =====================

DEC_Q = Decimal("0.01")


def eur_text_to_decimal(s: str) -> Decimal:
    s = s.strip()
    s = re.sub(r"[^\d,.\-]", "", s)
    if "," in s and s.count(",") == 1:
        s = s.replace(".", "").replace(",", ".")
    return Decimal(s or "0")


def almost_equal(a: Decimal, b: Decimal, tol: Decimal = DEC_Q) -> bool:
    return (a - b).copy_abs() <= tol


def normalize_money(m: Money) -> Decimal:
    """
    Prefiere parsear desde raw cuando:
      - raw tiene signo ('-' o '+'), o
      - el valor parseado desde raw es no-cero.
    Si no, usa value.
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
    chunks = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            chunks.append(page.get_text("text") or "")
    return "\n".join(chunks).strip()


# --- Normalización texto para evidencias ---


def _normalize_for_match(s: str) -> str:
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


def _is_numeric_snippet(s: str) -> bool:
    return bool(re.search(r"\d", s or ""))


def _any_numeric_snippet_present(snippets: list[str], full_text: str) -> bool:
    norm_text = _normalize_for_match(full_text)
    for snip in snippets or []:
        if _is_numeric_snippet(snip):
            if _normalize_for_match(snip) in norm_text:
                return True
    return False


# Detectar descuentos por línea
def detect_line_level_discounts(full_text: str) -> list[Decimal]:
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


# Detectar retenciones (IRPF/Retención Fiscal)
def detect_withholding(full_text: str) -> Dict[str, Decimal]:
    """
    Detecta 'Retención Fiscal 19% -81,20 €', 'Retencion IRPF 15 %', etc.
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
    sys_msg = (
        "Eres un extractor estricto de facturas. "
        "Responde EXCLUSIVAMENTE en JSON (sin texto adicional) siguiendo el esquema solicitado."
    )

    # prompt multimodal
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

    # 1) PDF -> imágenes
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

    # 2) Prompt (incluye retención)
    prompt = (
        "Extrae SOLO lo que ves en la factura (imágenes). Devuelve JSON con:\n"
        "- currency (ej: 'EUR')\n"
        "- subtotal {raw, value}\n"
        "- tax_amount {raw, value}\n"
        "- discount_amount {raw, value}\n"
        "- withholding_amount {raw, value}  # Retención (IRPF)\n"
        "- total {raw, value}\n"
        "- tax_rate_percent (porcentaje total de IVA)\n"
        "- withholding_rate_percent (porcentaje de retención, si existe)\n"
        "- evidence: para cada campo, arrays de cadenas EXACTAS visibles (p.ej. 'I.V.A. 21 %', 'Retención Fiscal 19% -81,20 €').\n\n"
        "Reglas:\n"
        "1) El % de IVA debe coincidir con lo visible (p.ej. 'I.V.A. 21 %').\n"
        "2) Si hay retención, se resta al total a pagar (no reduce la base de IVA).\n"
        "3) Si hay descuento de totales, resta al subtotal antes del IVA.\n"
        "4) 'raw' debe ser exactamente como se ve (coma/punto, símbolo, separadores).\n"
        "5) 'value' debe ser numérico con punto decimal.\n"
        "6) Prioriza la tabla/pie de totales si hay conflicto.\n"
    )

    # 3) Llamada al modelo
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

    # 4) Validaciones y enriquecimiento

    # 4a) Texto embebido + detectores
    full_text = ""
    try:
        full_text = extract_text_with_pymupdf(file_bytes)
    except Exception:
        full_text = ""

    line_discounts = detect_line_level_discounts(full_text)
    withholding_detected = detect_withholding(full_text)
    has_withholding_in_text = bool(withholding_detected)

    # Evidencias según política
    missing_evidence: Dict[str, List[str]] = {}
    if full_text and settings.EVIDENCE_POLICY != "off":
        missing_evidence = check_evidence_in_text(parsed.evidence, full_text)
        if settings.EVIDENCE_POLICY == "numbers":
            if "tax_rate_percent" in missing_evidence:
                del missing_evidence["tax_rate_percent"]
            for fld in ["subtotal", "tax_amount", "total", "withholding_amount"]:
                if fld in missing_evidence:
                    if _any_numeric_snippet_present(
                        parsed.evidence.get(fld, []), full_text
                    ):
                        del missing_evidence[fld]

    # 4b) Números normalizados
    sub = normalize_money(parsed.subtotal)
    tax = normalize_money(parsed.tax_amount)
    disc = normalize_money(parsed.discount_amount)
    ttl = normalize_money(parsed.total)
    wh = normalize_money(parsed.withholding_amount)

    # 4c) Reconciliación robusta: descuento + retención
    total_sans_adj = (sub + tax).quantize(DEC_Q, rounding=ROUND_HALF_UP)
    total_with_disc = (sub - disc + tax).quantize(DEC_Q, rounding=ROUND_HALF_UP)
    total_with_wh = (sub - wh + tax).quantize(DEC_Q, rounding=ROUND_HALF_UP)
    total_full = (sub - disc - wh + tax).quantize(DEC_Q, rounding=ROUND_HALF_UP)

    disc_eff = disc
    wh_eff = wh

    if almost_equal(ttl, total_full):
        pass  # usa ambos tal cual
    elif almost_equal(ttl, total_with_disc):
        wh_eff = Decimal("0")
    elif almost_equal(ttl, total_with_wh):
        disc_eff = Decimal("0")
    elif almost_equal(ttl, total_sans_adj):
        disc_eff = Decimal("0")
        wh_eff = Decimal("0")
    else:
        # Inferir delta faltante
        delta = (sub + tax - ttl).quantize(
            DEC_Q, rounding=ROUND_HALF_UP
        )  # cuánto hay que restar
        if delta >= Decimal("0"):
            # Preferencia: si el texto indica retención y el modelo no la trajo bien, asigna a retención
            if has_withholding_in_text and (wh == 0 or almost_equal(delta, wh)):
                wh_eff = delta
                disc_eff = Decimal("0")
                parsed.notes = (
                    parsed.notes + " | " if parsed.notes else ""
                ) + f"Retención inferida a partir de totales: {delta}"
            # Si el modelo trajo ambos y suman delta, úsalo
            elif (disc + wh) == delta:
                disc_eff, wh_eff = disc, wh
            # Si solo cuadra con descuento
            elif disc > 0 and almost_equal(delta, disc):
                disc_eff = disc
                wh_eff = Decimal("0")
                parsed.notes = (
                    parsed.notes + " | " if parsed.notes else ""
                ) + f"Descuento confirmado por totales: {disc}"
            # Si solo cuadra con retención
            elif wh > 0 and almost_equal(delta, wh):
                wh_eff = wh
                disc_eff = Decimal("0")
                parsed.notes = (
                    parsed.notes + " | " if parsed.notes else ""
                ) + f"Retención confirmada por totales: {wh}"
            else:
                # Reparto heurístico: si hay retención detectada en texto, toma todo como retención; si no, descuento
                if has_withholding_in_text:
                    wh_eff = delta
                    disc_eff = Decimal("0")
                    parsed.notes = (
                        parsed.notes + " | " if parsed.notes else ""
                    ) + f"Retención inferida a partir de totales: {delta}"
                else:
                    disc_eff = delta
                    wh_eff = Decimal("0")
                    parsed.notes = (
                        parsed.notes + " | " if parsed.notes else ""
                    ) + f"Descuento inferido a partir de totales: {delta}"
        # si delta < 0, dejaremos mismatch abajo

    computed_total = (sub - disc_eff - wh_eff + tax).quantize(
        DEC_Q, rounding=ROUND_HALF_UP
    )
    math_ok = almost_equal(ttl, computed_total)

    # 4d) % IVA: retención NO reduce base, descuento SÍ
    base_for_vat = max(Decimal("0"), (sub - disc_eff))
    computed_rate = (
        ((tax / base_for_vat) * Decimal("100")).quantize(Decimal("0.01"))
        if base_for_vat > 0
        else Decimal("0")
    )
    rate_ok = almost_equal(parsed.tax_rate_percent, computed_rate, Decimal("0.1"))

    # 4e) % Retención si procede (si no vino o vino 0 y tenemos wh_eff, infiere)
    wh_rate_reported = Decimal(
        str(getattr(parsed, "withholding_rate_percent", Decimal("0")))
    )
    wh_rate_ok = True
    computed_wh_rate = Decimal("0")
    if wh_eff > 0 and sub > 0:
        computed_wh_rate = ((wh_eff / sub) * Decimal("100")).quantize(Decimal("0.01"))
        if wh_rate_reported > 0:
            wh_rate_ok = almost_equal(
                wh_rate_reported, computed_wh_rate, Decimal("0.1")
            )
        else:
            # si el modelo no lo trajo, completamos el campo
            parsed.withholding_rate_percent = computed_wh_rate

    problems = []
    warnings = []

    # Evidencias: solo rompen en strict
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
    # Validación de tasa de retención (si aplica)
    if wh_eff > 0 and wh_rate_reported > 0 and not wh_rate_ok:
        problems.append(
            {
                "type": "withholding_rate_mismatch",
                "expected_rate_percent": str(computed_wh_rate),
                "reported_rate_percent": str(wh_rate_reported),
            }
        )

    # Notas informativas
    if line_discounts:
        msg = f"Descuentos por línea detectados: [{', '.join(f'{d:.2f}%' for d in line_discounts)}]"
        if disc_eff == 0 and disc > 0:
            msg += ". El descuento informado no afecta a los totales."
        elif disc_eff == 0 and disc == 0:
            msg += ". No afectan al total final."
        parsed.notes = (parsed.notes + " | " + msg) if parsed.notes else msg

    if wh_eff > 0:
        msg = "Retención detectada"
        if has_withholding_in_text and "percent" in withholding_detected:
            msg += f" {withholding_detected['percent']}%"
        msg += f" por {wh_eff}"
        if computed_wh_rate > 0:
            msg += f" (≈ {computed_wh_rate}%)"
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
