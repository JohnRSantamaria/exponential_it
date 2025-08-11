# parser_document.py

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
    # NUEVO: Retenciones fiscales (IRPF, 'Retención Fiscal', etc.)
    withholding_amount: Money = Field(
        default_factory=lambda: Money(raw="0", value=Decimal("0.00")),
        description="Importe total de retenciones. Suele verse como negativo en el documento.",
    )
    withholding_rate_percent: Decimal = Field(
        default=Decimal("0.0"),
        description="Porcentaje de retención si aparece impreso (p.ej. 19.0).",
    )
    # Evidencias: recortes textuales que el modelo vio en el documento
    evidence: Dict[str, List[str]] = Field(
        ..., description="Evidencias por campo (ej: {'total': ['TOTAL 7.685,38 €']})"
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
    s = re.sub(r"[^\d,.\-+]", "", s)
    # Si hay coma como separador decimal, elimina puntos de miles
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


# ==== Helpers extra: formateo y evidencia sintética ====


def format_eur_es(v: Decimal) -> str:
    """
    Devuelve número con formato español: 1234.56 -> '1.234,56 €'
    """
    q = Decimal("0.01")
    vq = v.quantize(q)
    s = f"{vq:.2f}"  # 1234.56
    entero, dec = s.split(".")
    # miles
    entero_rev = entero[::-1]
    grupos = [entero_rev[i : i + 3] for i in range(0, len(entero_rev), 3)]
    entero_fmt = ".".join(g[::-1] for g in grupos[::-1])
    return f"{entero_fmt},{dec} €"


def _add_evidence_snippet(evidence: Dict[str, List[str]], key: str, snippet: str):
    if not snippet:
        return
    evidence.setdefault(key, [])
    if snippet not in evidence[key]:
        evidence[key].append(snippet)


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


# Detectar retenciones (IRPF, Retención Fiscal, etc.) mejorado
RET_WITHHOLD_RE = re.compile(
    r"(?:retenci[óo]n(?:\s+(?:fiscal|irpf))?|irpf|ret\.)"
    r"[^%\n\r]*?(\d{1,2}(?:[.,]\d+)?)\s*%"  # porcentaje
    r"[^0-9\-+]*"  # relleno
    r"([-+]?[\d.\s]+(?:[.,]\d{2}))?",  # importe opcional
    re.IGNORECASE,
)


def detect_withholding(full_text: str) -> Dict[str, Decimal]:
    """
    Detecta retenciones tipo 'Retención Fiscal 19% -81,20 €', 'IRPF 15 %'.
    Devuelve {'percent': Decimal|None, 'amount': Decimal|None} si detecta algo, o {}.
    """
    out: Dict[str, Decimal] = {}
    if not full_text:
        return out
    m = RET_WITHHOLD_RE.search(full_text)
    if not m:
        return out
    try:
        out["percent"] = Decimal(m.group(1).replace(",", "."))
    except Exception:
        pass
    amt = m.group(2)
    if amt:
        try:
            out["amount"] = eur_text_to_decimal(amt)
        except Exception:
            pass
    return out


# ===================== Prompt + JSON Schema para salida =====================

PROMPT_INVOICE = (
    "Eres un extractor estricto de FACTURAS. Responde EXCLUSIVAMENTE en JSON válido "
    "(sin texto extra) con este esquema y reglas. Analiza SOLO lo que ves en las imágenes:\n\n"
    "ESQUEMA:\n"
    '- currency: string (p.ej. "EUR")\n'
    "- subtotal: { raw: string, value: number }\n"
    "- tax_amount: { raw: string, value: number }\n"
    "- discount_amount: { raw: string, value: number }\n"
    "- total: { raw: string, value: number }\n"
    "- tax_rate_percent: number\n"
    "- withholding_amount: { raw: string, value: number }\n"
    "- withholding_rate_percent: number\n"
    "- evidence: object (para cada campo anterior, lista de cadenas EXACTAS vistas)\n"
    "- notes: string|null\n\n"
    "REGLAS:\n"
    "1) Distingue “descuento” (reduce base de IVA) vs “retención/IRPF” (NO reduce base; solo baja el total).\n"
    "2) Consolida descuentos por línea en discount_amount.\n"
    "3) Si aparece “Retención Fiscal/IRPF”, rellena withholding_amount y withholding_rate_percent.\n"
    "4) 'raw' EXACTO; 'value' numérico con punto decimal.\n"
    "5) Prioriza el cuadro de TOTALES.\n"
    "6) evidence debe incluir, para CADA campo, al menos un fragmento que contenga su NÚMERO correspondiente (por ejemplo, 'TOTAL EUROS 435,93 €', 'I.V.A. 21 % 89,75 €', 'Retención Fiscal 19% -81,20 €'). Evita evidencias sin cifra.\n"
    "7) NO OMITEAS NINGÚN CAMPO. Si no existe en la factura: discount_amount.value=0, withholding_amount.value=0, withholding_rate_percent=0.\n"
    "8) NO uses null salvo en notes. NO uses strings para números; usa number.\n"
    '9) Ejemplo de retención: withholding_amount.raw="-81,20 €", withholding_amount.value=-81.20, withholding_rate_percent=19.\n'
)

MONEY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "raw": {"type": "string"},
        "value": {"type": "number"},
    },
    "required": ["raw", "value"],
}

INVOICE_JSON_SCHEMA = {
    "name": "invoice_totals",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "currency": {"type": "string"},
            "subtotal": MONEY_SCHEMA,
            "tax_amount": MONEY_SCHEMA,
            "discount_amount": MONEY_SCHEMA,
            "total": MONEY_SCHEMA,
            "tax_rate_percent": {"type": "number"},
            "withholding_amount": MONEY_SCHEMA,
            "withholding_rate_percent": {"type": "number"},
            "evidence": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "notes": {"type": ["string", "null"]},
        },
        "required": [
            "currency",
            "subtotal",
            "tax_amount",
            "discount_amount",
            "total",
            "tax_rate_percent",
            "withholding_amount",
            "withholding_rate_percent",
            "evidence",
        ],
    },
}

# ============ Parcheo post-modelo para garantizar tipos y defaults ============


def _ensure_money(obj: dict, field: str):
    if field not in obj or not isinstance(obj[field], dict):
        obj[field] = {"raw": "0", "value": 0.0}
    else:
        obj[field].setdefault("raw", "0")
        v = obj[field].get("value", 0.0)
        if isinstance(v, str):
            vv = v.strip().replace(",", ".")
            try:
                v = float(vv)
            except Exception:
                v = 0.0
        obj[field]["value"] = float(v)


def _coerce_number(obj: dict, field: str):
    if field in obj:
        v = obj[field]
        if isinstance(v, str):
            vv = v.strip().replace(",", ".")
            try:
                obj[field] = float(vv)
            except Exception:
                obj[field] = 0.0


def _patch_and_validate_invoice_json(json_text: str) -> InvoiceTotals:
    try:
        data = json.loads(json_text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"JSON inválido del modelo: {e}")

    # Asegurar objetos Money presentes
    for fld in [
        "subtotal",
        "tax_amount",
        "discount_amount",
        "total",
        "withholding_amount",
    ]:
        _ensure_money(data, fld)

    # Números siempre numéricos
    for fld in ["tax_rate_percent", "withholding_rate_percent"]:
        _coerce_number(data, fld)

    # Defaults si faltan
    data.setdefault("currency", "EUR")
    ev = data.setdefault("evidence", {})
    # Claves base en evidence para posteriores enriquecimientos
    for k in [
        "subtotal",
        "tax_amount",
        "discount_amount",
        "total",
        "tax_rate_percent",
        "withholding_amount",
        "withholding_rate_percent",
    ]:
        ev.setdefault(k, [])
    data.setdefault("notes", None)

    # Validación final Pydantic (lanza ValidationError si algo no cuadra)
    try:
        return InvoiceTotals.model_validate(data)
    except ValidationError as ve:
        logger.error(
            f"Estructura tras parcheo no valida: {json.dumps(data, ensure_ascii=False)}"
        )
        raise ve


# ===================== OpenAI (Chat Completions con imágenes y JSON) =====================


async def _call_openai_for_invoice_with_images(
    client: AsyncOpenAI,
    user_prompt: str,
    image_data_uris: list[str],
) -> InvoiceTotals:
    """
    Envía 1..N imágenes (data URIs PNG) + prompt. Intenta salida con JSON Schema,
    y si falla, hace fallback a json_object. Luego se parchea y valida con Pydantic.
    """
    sys_msg = (
        "Eres un extractor estricto de facturas. "
        "Responde EXCLUSIVAMENTE en JSON (sin texto adicional) siguiendo el esquema solicitado."
    )

    content: list[dict] = [{"type": "text", "text": user_prompt}]
    for uri in image_data_uris:
        content.append({"type": "image_url", "image_url": {"url": uri}})

    # 1) Intento: schema estricto
    try:
        chat = await client.chat.completions.create(
            model=getattr(settings, "CHAT_MODEL", settings.MODEL_NAME),
            response_format={"type": "json_schema", "json_schema": INVOICE_JSON_SCHEMA},
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": content},
            ],
            temperature=0,
        )
        json_text = chat.choices[0].message.content
    except Exception:
        # 2) Fallback: json_object normal
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

    return _patch_and_validate_invoice_json(json_text)


# ===================== Servicio principal =====================


@router.post("/extract-invoice", response_model=InvoiceTotals)
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

    # 2) Prompt multimodal
    prompt = PROMPT_INVOICE

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
    withholding_text = detect_withholding(full_text)
    is_withholding = bool(withholding_text)

    # Evidencias segun política
    missing_evidence: Dict[str, List[str]] = {}
    evidence_policy = getattr(
        settings, "EVIDENCE_POLICY", "numbers"
    )  # off | numbers | strict
    if full_text and evidence_policy != "off":
        missing_evidence = check_evidence_in_text(parsed.evidence, full_text)

        if evidence_policy == "numbers":
            # si hay números en evidencias, damos por bueno
            for fld in [
                "subtotal",
                "tax_amount",
                "discount_amount",
                "total",
                "tax_rate_percent",
                "withholding_amount",
                "withholding_rate_percent",
            ]:
                if fld in missing_evidence:
                    if _any_numeric_snippet_present(
                        parsed.evidence.get(fld, []), full_text
                    ):
                        del missing_evidence[fld]

    # 4b) Aritmética y % impuestos
    sub = normalize_money(parsed.subtotal)
    tax = normalize_money(parsed.tax_amount)
    disc_reported = normalize_money(parsed.discount_amount)
    ttl = normalize_money(parsed.total)

    # Retención: puede venir con signo en raw. Lo tomamos tal cual como "efecto" sobre el total.
    wh = normalize_money(parsed.withholding_amount)
    wh_effective = (
        wh  # si quieres forzar que siempre reste, usa: wh_effective = -abs(wh)
    )

    # --- RECONCILIACIÓN DE DESCUENTO / RETENCIÓN (robusta) ---
    computed_total_no_disc_no_wh = (sub + tax).quantize(DEC_Q, rounding=ROUND_HALF_UP)
    computed_total_with_disc_no_wh = (sub - disc_reported + tax).quantize(
        DEC_Q, rounding=ROUND_HALF_UP
    )

    if almost_equal(ttl, computed_total_no_disc_no_wh + wh_effective):
        disc_effective = Decimal("0")
    elif almost_equal(ttl, computed_total_with_disc_no_wh + wh_effective):
        disc_effective = disc_reported
    else:
        # Infiera "descuento" adicional si hace cuadrar (retención ya está considerada en wh_effective)
        inferred = (sub + tax + wh_effective - ttl).quantize(
            DEC_Q, rounding=ROUND_HALF_UP
        )
        if inferred >= Decimal("0") and almost_equal(
            ttl,
            (sub - inferred + tax + wh_effective).quantize(
                DEC_Q, rounding=ROUND_HALF_UP
            ),
        ):
            disc_effective = inferred
            note = f"Descuento inferido a partir de totales: {inferred}"
            parsed.notes = (parsed.notes + " | " + note) if parsed.notes else note
        else:
            disc_effective = disc_reported  # quedará mismatch

    computed_total = (sub - disc_effective + tax + wh_effective).quantize(
        DEC_Q, rounding=ROUND_HALF_UP
    )
    math_ok = almost_equal(ttl, computed_total)

    # --- Tasa de IVA: la retención NO reduce la base; el descuento SÍ ---
    base_for_vat = max(Decimal("0"), (sub - disc_effective))
    computed_rate = (
        ((tax / base_for_vat) * Decimal("100")).quantize(Decimal("0.01"))
        if base_for_vat > 0
        else Decimal("0")
    )
    rate_ok = almost_equal(parsed.tax_rate_percent, computed_rate, Decimal("0.1"))

    # ---- ENRIQUECIMIENTO DE EVIDENCIAS Y RETENCIÓN ----
    # 4.1. Evidencias con números para subtotal, tax, total
    if full_text:

        def _ensure_numeric_evidence(key: str, label: str, money: Decimal):
            has_num = any(_is_numeric_snippet(s) for s in parsed.evidence.get(key, []))
            if not has_num:
                _add_evidence_snippet(
                    parsed.evidence, key, f"{label} {format_eur_es(money)}"
                )

        _ensure_numeric_evidence("subtotal", "Subtotal", sub)
        _ensure_numeric_evidence("tax_amount", "I.V.A.", tax)
        _ensure_numeric_evidence("total", "TOTAL", ttl)

    # 4.2. Retención: inferir/actualizar evidencias y valores si faltan
    inferred_wh = (ttl - (sub - disc_effective + tax)).quantize(
        DEC_Q, rounding=ROUND_HALF_UP
    )

    if is_withholding or (inferred_wh != 0):
        # Si el valor del objeto es 0 pero hay inferido, actualiza el objeto:
        if almost_equal(wh_effective, Decimal("0")) and inferred_wh != 0:
            try:
                parsed.withholding_amount = Money(
                    raw=format_eur_es(inferred_wh), value=inferred_wh
                )
                wh_effective = inferred_wh
            except Exception:
                pass

        # Evidence para porcentaje
        if "percent" in withholding_text and withholding_text["percent"] is not None:
            _add_evidence_snippet(
                parsed.evidence,
                "withholding_rate_percent",
                f"Retención Fiscal {withholding_text['percent']}%",
            )
        elif parsed.withholding_rate_percent and parsed.withholding_rate_percent != 0:
            _add_evidence_snippet(
                parsed.evidence,
                "withholding_rate_percent",
                f"Retención Fiscal {parsed.withholding_rate_percent}%",
            )

        # Evidence para importe
        has_num_wh = any(
            _is_numeric_snippet(s)
            for s in parsed.evidence.get("withholding_amount", [])
        )
        if not has_num_wh and not almost_equal(wh_effective, Decimal("0")):
            pct = None
            if (
                "percent" in withholding_text
                and withholding_text["percent"] is not None
            ):
                pct = withholding_text["percent"]
            elif (
                parsed.withholding_rate_percent and parsed.withholding_rate_percent != 0
            ):
                pct = parsed.withholding_rate_percent

            if pct is not None:
                snippet = f"Retención Fiscal {pct}% {format_eur_es(wh_effective)}"
            else:
                snippet = f"Retención {format_eur_es(wh_effective)}"
            _add_evidence_snippet(parsed.evidence, "withholding_amount", snippet)

    # 4.3. Asegurar evidencia numérica para tax_rate_percent
    has_num_rate = any(
        _is_numeric_snippet(s) for s in parsed.evidence.get("tax_rate_percent", [])
    )
    if not has_num_rate and computed_rate != 0:
        _add_evidence_snippet(
            parsed.evidence, "tax_rate_percent", f"IVA {computed_rate}%"
        )

    problems = []
    warnings = []

    # Evidencias: solo rompen en modo strict
    if full_text and evidence_policy == "strict":
        # recalcula missing tras enriquecimiento
        missing_evidence = check_evidence_in_text(parsed.evidence, full_text)
        if missing_evidence:
            problems.append({"type": "evidence_missing", "details": missing_evidence})
    elif full_text and evidence_policy == "numbers":
        # recalcula y si aún falta, warning
        missing_evidence = check_evidence_in_text(parsed.evidence, full_text)
        if missing_evidence:
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
        if disc_effective == 0 and disc_reported > 0:
            msg += ". El descuento informado no afecta a los totales."
        elif disc_effective == 0 and disc_reported == 0:
            msg += ". No afectan al total final."
        parsed.notes = (parsed.notes + " | " + msg) if parsed.notes else msg

    if is_withholding or (inferred_wh != 0):
        msg = "Retención detectada"
        if "percent" in withholding_text:
            msg += f" {withholding_text['percent']}%"
            # (opcional) comprobación simple de coherencia con base_for_vat:
            if base_for_vat > 0:
                expected_wh = (
                    base_for_vat * (withholding_text["percent"] / Decimal("100"))
                ).quantize(DEC_Q)
                if wh_effective != 0 and not almost_equal(
                    expected_wh.copy_abs(), wh_effective.copy_abs(), DEC_Q
                ):
                    msg += f". Diferencia esperada vs reportada: {expected_wh} vs {wh_effective}"
        if "amount" in withholding_text:
            msg += f" por {withholding_text['amount']}"
        # Si no hay amount en texto y lo inferimos, ya actualizamos arriba. Refleja en nota:
        if ("amount" not in withholding_text) and inferred_wh:
            msg += f". Importe inferido: {inferred_wh}"
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
