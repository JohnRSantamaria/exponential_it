from decimal import Decimal, InvalidOperation
import io
from typing import Any, Optional, Set, Iterable
from PIL import Image
from exponential_core.exceptions import CustomAppException
from app.services.taggun.exceptions import ImageTooSmall, UnsupportedImageFormatError


# -------------------- Imagen --------------------


def validate_image_dimensions(
    filename: str, file_bytes: bytes, min_width: int = 100, min_height: int = 100
):
    """Valida que el archivo sea una imagen con dimensiones mínimas. Si es PDF, no valida."""
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    supported_extensions = {"jpg", "jpeg", "png", "bmp", "tiff", "webp"}

    # Si es PDF, no valida dimensiones
    if ext == "pdf":
        return

    if ext not in supported_extensions:
        raise UnsupportedImageFormatError(ext, sorted(supported_extensions))

    # Intentar abrir la imagen de forma segura
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
    except Exception as e:
        raise CustomAppException(f"No se pudo procesar la imagen: {e}")

    if width < min_width or height < min_height:
        raise ImageTooSmall(width, height, min_width, min_height)


# -------------------- Decimals / Porcentajes --------------------


def _to_decimal(val: Any) -> Optional[Decimal]:
    """Convierte val a Decimal de forma robusta (acepta str/int/float/Decimal)."""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return None


def _iterable(obj: Any) -> bool:
    return isinstance(obj, (set, list, tuple))


def to_tax_candidates(value: Any) -> Optional[Set[Decimal]]:
    """
    Convierte:
      - None -> None
      - escalar numérico/str -> {Decimal(valor)}
      - iterable de numéricos/str -> {Decimal(...), ...}
    Descarta entradas no convertibles.
    """
    if value is None:
        return None

    if not _iterable(value):
        d = _to_decimal(value)
        return {d} if d is not None else None

    # Colección
    decs: Set[Decimal] = set()
    for v in value:
        d = _to_decimal(v)
        if d is not None:
            decs.add(d)
    return decs or None


def rate_from_amounts(amount_untaxed: Any, amount_tax: Any) -> Decimal:
    """
    % IVA a partir de importes (magnitud). Soporta notas de crédito.
    """
    sub = _to_decimal(amount_untaxed) or Decimal("0")
    tax = _to_decimal(amount_tax) or Decimal("0")
    base = sub.copy_abs()
    if base == 0:
        return Decimal("0.00")
    rate = (tax.copy_abs() / base) * Decimal("100")
    return rate.quantize(Decimal("0.01"))


def to_decimal_one(
    value_or_set: Any, *, quantize: bool = True, abs_value: bool = True
) -> Decimal:
    """
    Devuelve un único Decimal a partir de:
      - escalar numérico/str/Decimal
      - iterable (set/list/tuple) de los anteriores
    Si es iterable con múltiples valores, elige de forma **determinística** el menor.
    Parámetros:
      - quantize: redondea a 2 decimales (útil para %).
      - abs_value: retorna magnitud (True para porcentajes).
    """
    if _iterable(value_or_set):
        decs = [d for d in (_to_decimal(v) for v in value_or_set) if d is not None]
        if not decs:
            return Decimal("0.00") if quantize else Decimal("0")
        val = min(decs)  # determinístico para sets
    else:
        val = _to_decimal(value_or_set) or Decimal("0")

    if abs_value:
        val = val.copy_abs()
    if quantize:
        val = val.quantize(Decimal("0.01"))
    return val


def take_single_percent(singleton: set[Decimal] | None) -> Decimal | None:
    """De un set {Decimal('xx')} devuelve Decimal('xx.xx') normalizado; None si viene vacío/None."""
    if not singleton:
        return None
    d = next(iter(singleton))
    if not isinstance(d, Decimal):
        d = Decimal(str(d))
    return d.copy_abs().quantize(Decimal("0.01"))
