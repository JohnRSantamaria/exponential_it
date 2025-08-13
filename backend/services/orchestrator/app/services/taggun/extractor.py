from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, getcontext
from typing import Dict, Optional, Set, List, Any, Iterable

from app.core.settings import settings
from app.core.logging import logger
from app.services.zoho.exceptions import TaxPercentageNotFound
from app.services.taggun.schemas.taggun_models import (
    AddressSchema,
    LineItemSchema,
    TaggunExtractedInvoiceBasic,
)

# Aumenta precisión global (el redondeo a 2 decimales lo maneja quant2)
getcontext().prec = 38


def D(val: Any, default: str = "0") -> Decimal:
    """
    Conversión segura a Decimal:
    - Si ya es Decimal, retorna tal cual.
    - Si es float -> usa str(valor) para evitar binario.
    - Si es str -> normaliza coma decimal a punto; strip.
    - Si falla -> retorna Decimal(default).
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


class TaggunExtractor:
    def __init__(self, payload: dict):
        self.ocr_data = payload
        self.candidates: Set[Decimal] = set()
        self.corrected_values: Dict[str, Decimal] = {}

        # Convierte tasas estándar a Decimal una sola vez
        self._standard_rates: List[Decimal] = [
            D(r) for r in getattr(settings, "TAX_STANDARD_RATES", [])
        ]

        # Tolerancias como Decimal
        self._rate_tolerance: Decimal = Decimal("0.30")  # tolerancia en % de tasa
        self._sum_tolerance: Decimal = Decimal("0.05")  # tolerancia en dinero

    # -----------------------
    # Utils
    # -----------------------
    @staticmethod
    def parse_iso_date(value: str):
        """
        Intenta convertir una cadena ISO (p.ej. '2024-01-01T00:00:00Z') en date.
        Retorna None si no es válida.
        """
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except Exception:
            return None

    def normalize(
        self, value: Decimal, tolerance: Decimal = Decimal("0.03")
    ) -> Decimal:
        """
        Redondea a 2 decimales y aproxima a la tasa estándar más cercana
        dentro de una tolerancia (en puntos porcentuales, p.ej. 0.03).
        """
        rounded = quant2(value)
        for standard in self._standard_rates:
            if abs(rounded - standard) <= tolerance:
                return standard
        return rounded

    @staticmethod
    def _majority_gate(
        amount_untaxed: Decimal, amount_total: Decimal, amount_tax: Decimal
    ) -> bool:
        """Al menos 2 de 3 montos deben ser > 0 para continuar."""
        return ((amount_untaxed > 0) + (amount_total > 0) + (amount_tax > 0)) >= 2

    def _raise_error(self):
        raise TaxPercentageNotFound()

    def _add_candidate(self, percentage: Decimal) -> None:
        normalized = self.normalize(percentage)
        # Acepta exactamente iguales a un estándar (o ya normalizado a él)
        if any(abs(normalized - r) <= Decimal("0.00") for r in self._standard_rates):
            self.candidates.add(normalized)

    def _compute_percentage(self, untaxed: Decimal, tax: Decimal) -> None:
        if untaxed <= 0:
            return
        percentage = quant2((tax / untaxed) * Decimal("100"))
        self._add_candidate(percentage)

    def _try_paths(self, *paths: Iterable[List[str]], default=""):
        """Intenta distintos paths dentro del payload OCR, retornando el primero que exista."""
        for path in paths:
            value: Any = self.ocr_data
            for key in path:
                try:
                    value = value[key]
                except (KeyError, TypeError):
                    value = None
                    break
            if value is not None:
                return value
        return default

    # -----------------------
    # Address
    # -----------------------
    def extract_address(self) -> AddressSchema:
        return AddressSchema(
            street=self._try_paths(["merchantAddress", "data"]),
            city=self._try_paths(["merchantCity", "data"]),
            state=self._try_paths(["merchantState", "data"]),
            country_code=self._try_paths(["merchantCountryCode", "data"]),
            postal_code=self._try_paths(["merchantPostalCode", "data"]),
            phone=self._try_paths(["merchantPhoneNumber", "data"]),
            fax=self._try_paths(["merchantFax", "data"]),
            email=self._try_paths(["merchantEmail", "data"]),
            website=self._try_paths(["merchantWebsite", "data"]),
        )

    # -----------------------
    # Line Items
    # -----------------------
    def extract_line_items(self) -> list:
        items = self._try_paths(["entities", "productLineItems"], default=[])
        return items if isinstance(items, list) else []

    def parse_line_items(
        self,
        amount_untaxed: Decimal,
    ) -> List[LineItemSchema]:
        """
        Devuelve ítems consistentes con el monto total global.
        Si la suma no coincide con amount_total, crea un solo ítem
        que cumpla con el total exacto (se ignoran descuentos).
        """
        raw_items = self.extract_line_items()
        parsed_items: List[LineItemSchema] = []

        EPS = self._sum_tolerance
        total_expected = quant2(amount_untaxed or Decimal("0"))

        products_name: List[str] = []
        sum_total: Decimal = Decimal("0")

        for item in raw_items:
            data = item.get("data", {}) or {}

            name = (data.get("name", {}) or {}).get("data", "") or ""
            qty = data.get("quantity", {}) or {}
            qty = qty.get("data", 0) or 0

            unit_price = D((data.get("unitPrice", {}) or {}).get("data"))
            total_price = D((data.get("totalPrice", {}) or {}).get("data"))

            # Normaliza tipos
            qty = int(qty) if isinstance(qty, int) else (qty or 0)
            unit_price = unit_price or Decimal("0")
            total_price = total_price or Decimal("0")

            products_name.append(name.strip())

            line_total = total_price if total_price > 0 else (unit_price * qty)
            sum_total += line_total

            parsed_items.append(
                LineItemSchema(
                    name=name.strip(),
                    quantity=qty,
                    unit_price=quant2(unit_price),
                    total_price=quant2(line_total),
                )
            )

        # 🔍 Validar si la suma coincide con amount_total
        if abs(sum_total - total_expected) > EPS or not parsed_items:
            logger.warning("No coincide la suma de los items con el total")
            # ❗ Forzamos un solo item que cuadre con amount_total
            merged_name = (
                ", ".join([n for n in products_name if n]) or "Conceptos varios"
            )
            return [
                LineItemSchema(
                    name=merged_name,
                    quantity=1,
                    unit_price=total_expected,
                    total_price=total_expected,
                )
            ]

        return parsed_items

    # -----------------------
    # Base values
    # -----------------------
    def extrac_base_values(self) -> TaggunExtractedInvoiceBasic:
        partner_name = self._try_paths(
            ["merchantName", "data"],
            ["entities", "merchantName", "data"],
        )

        partner_vat = self._try_paths(
            ["merchantTaxId", "data"],
            ["entities", "merchantVerification", "data", "verificationId"],
        )

        raw_date = self._try_paths(["date", "data"])
        date_invoice = self.parse_iso_date(raw_date)

        invoice_number = self._try_paths(
            ["invoiceNumber", "data"],
            ["entities", "invoiceNumber", "data"],
        )

        amount_total = D(self._try_paths(["totalAmount", "data"], default=0.0))
        amount_tax = D(self._try_paths(["taxAmount", "data"], default=0.0))
        amount_untaxed = D(self._try_paths(["paidAmount", "data"], default=0.0))
        amount_discount = D(self._try_paths(["discountAmount", "data"], default=0.0))
        amount_discount = abs(amount_discount)

        taggun_basic_fields = {
            "partner_name": partner_name,
            "partner_vat": partner_vat,
            "date": date_invoice,
            "invoice_number": invoice_number,
            "amount_total": quant2(amount_total),
            "amount_tax": quant2(amount_tax),
            "amount_untaxed": quant2(amount_untaxed),
            "amount_discount": quant2(amount_discount),
        }

        return TaggunExtractedInvoiceBasic(**taggun_basic_fields)

    # -----------------------
    # Tax candidates
    # -----------------------
    def calculate_tax_candidates(
        self,
        amount_untaxed: Decimal,
        amount_total: Decimal,
        amount_tax: Decimal,
        amount_discount: Optional[Decimal] = Decimal("0"),
    ) -> Set[Decimal]:
        """
        Calcula candidatos de tasa de impuesto.
        ✅ Blindado: convierte argumentos a Decimal al inicio.
        """
        # 🔹 Blindaje: siempre trabajar con Decimal, aunque entren float
        amount_untaxed = D(amount_untaxed)
        amount_total = D(amount_total)
        amount_tax = D(amount_tax)
        amount_discount = D(amount_discount)

        if not self._majority_gate(
            amount_tax=amount_tax,
            amount_total=amount_total,
            amount_untaxed=amount_untaxed,
        ):
            self._raise_error()

        u, t, tx, d = (
            amount_untaxed or Decimal("0"),
            amount_total or Decimal("0"),
            amount_tax or Decimal("0"),
            amount_discount or Decimal("0"),
        )

        rate_tol = self._rate_tolerance

        def is_valid_rate(untaxed: Decimal, tax: Decimal) -> bool:
            if untaxed <= 0:
                return False
            rate = quant2((tax / untaxed) * Decimal("100"))
            return any(abs(rate - r) <= rate_tol for r in self._standard_rates)

        # Caso 1: Descuento presente y todos los valores
        if d > 0 and u > 0 and tx > 0 and t > 0:
            expected_total = u - d + tx
            if abs(expected_total - t) > rate_tol:
                u2 = t - tx + d
                if is_valid_rate(u2, tx):
                    u = u2
                else:
                    self._raise_error()
            self._compute_percentage(u, tx)

            self.corrected_values = {
                "amount_untaxed": quant2(u),
                "amount_total": quant2(t),
                "amount_tax": quant2(tx),
            }
            return self.candidates

        # Caso 2: Descuento presente, falta uno de los tres
        if d > 0:
            if t > 0 and u > 0 and tx <= 0:
                tx = t - (u - d)
                if not is_valid_rate(u, tx):
                    self._raise_error()
                self._compute_percentage(u, tx)

                self.corrected_values = {
                    "amount_untaxed": quant2(u),
                    "amount_total": quant2(t),
                    "amount_tax": quant2(tx),
                }
                return self.candidates

            elif t > 0 and tx > 0 and u <= 0:
                u = t - tx + d
                if not is_valid_rate(u, tx):
                    self._raise_error()
                self._compute_percentage(u, tx)

                self.corrected_values = {
                    "amount_untaxed": quant2(u),
                    "amount_total": quant2(t),
                    "amount_tax": quant2(tx),
                }
                return self.candidates

            elif u > 0 and tx > 0 and t <= 0:
                t = u - d + tx
                if not is_valid_rate(u, tx):
                    self._raise_error()
                self._compute_percentage(u, tx)

                self.corrected_values = {
                    "amount_untaxed": quant2(u),
                    "amount_total": quant2(t),
                    "amount_tax": quant2(tx),
                }
                return self.candidates

        # Caso 3: Sin descuento, todos los valores presentes
        if t > 0 and u > 0 and tx > 0:
            if abs((u + tx) - t) > rate_tol:
                expected_untaxed = t - tx
                expected_total = u + tx

                rate_if_untaxed_fixed = (
                    quant2((tx / expected_untaxed) * Decimal("100"))
                    if expected_untaxed > 0
                    else Decimal("-1")
                )
                rate_if_total_fixed = (
                    quant2((tx / u) * Decimal("100")) if u > 0 else Decimal("-1")
                )

                match_untaxed = any(
                    abs(rate_if_untaxed_fixed - r) <= rate_tol
                    for r in self._standard_rates
                )
                match_total = any(
                    abs(rate_if_total_fixed - r) <= rate_tol
                    for r in self._standard_rates
                )

                if match_untaxed and not match_total:
                    u = expected_untaxed
                elif match_total and not match_untaxed:
                    t = expected_total
                elif match_untaxed and match_total:
                    # Ambos cuadran, se prefiere mantener el total
                    u = expected_untaxed
                else:
                    self._raise_error()

            if not is_valid_rate(u, tx):
                self._raise_error()

            self._compute_percentage(u, tx)

            self.corrected_values = {
                "amount_untaxed": quant2(u),
                "amount_total": quant2(t),
                "amount_tax": quant2(tx),
            }
            return self.candidates

        # Caso 4: Falta tax
        if t > 0 and u > 0 and tx <= 0:
            tx = t - u
            if not is_valid_rate(u, tx):
                self._raise_error()
            self._compute_percentage(u, tx)

        # Caso 5: Falta untaxed
        elif t > 0 and u <= 0 and tx > 0:
            u = t - tx
            if not is_valid_rate(u, tx):
                self._raise_error()
            self._compute_percentage(u, tx)

        # Caso 6: Falta total
        elif t <= 0 and u > 0 and tx > 0:
            t = u + tx
            if not is_valid_rate(u, tx):
                self._raise_error()
            self._compute_percentage(u, tx)

        else:
            self._raise_error()

        self.corrected_values = {
            "amount_untaxed": quant2(u),
            "amount_total": quant2(t),
            "amount_tax": quant2(tx),
        }

        return self.candidates
