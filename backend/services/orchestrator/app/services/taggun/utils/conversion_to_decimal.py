from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from app.services.taggun.exceptions import FieldNotFoundError


def D(val: Any, default: str = "0") -> Decimal:
    """
    Conversión segura a Decimal:
    - Decimal -> tal cual
    - float -> Decimal(str(valor)) para evitar binario
    - int -> Decimal(int)
    - str -> normaliza coma decimal a punto, strip
    - None / inválidos -> Decimal(default)
    """
    if isinstance(val, Decimal):
        return val
    try:
        if val is None:
            return Decimal(default)
        if isinstance(val, float):
            return Decimal(str(val))
        if isinstance(val, int):
            return Decimal(val)
        if isinstance(val, str):
            s = val.strip().replace(",", ".")
            if s == "":
                return Decimal(default)
            return Decimal(s)
        return Decimal(default)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def quant2(x: Decimal) -> Decimal:
    """Redondeo financiero a 2 decimales con HALF_UP."""
    return D(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def f2(x: Decimal) -> float:
    """
    Devuelve float redondeado a 2 decimales (para los modelos Pydantic que esperan float).
    Mantiene los cálculos internamente en Decimal.
    """
    return float(quant2(x))


def _require(value: Any, field_name: str):
    """Valida presencia de campos obligatorios y lanza FieldNotFoundError."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise FieldNotFoundError(field_name)
    return value
