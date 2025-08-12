import re
from typing import Dict, List
import fitz  # PyMuPDF
import base64
import unicodedata

from decimal import Decimal
from exponential_core.openai import MoneySchema

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


def normalize_money(m: MoneySchema) -> Decimal:
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
