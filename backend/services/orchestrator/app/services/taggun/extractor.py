from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, getcontext
from typing import Dict, Optional, Set, List, Any, Iterable

from app.core.settings import settings
from app.services.taggun.exceptions import (
    FieldNotFoundError,
    LineItemsSumMismatchError,
    MissingRequiredAmountsError,
    OCRPayloadFormatError,
)
from app.services.taggun.utils.conversion_to_decimal import D, _require, f2, quant2
from app.services.zoho.exceptions import TaxPercentageNotFound
from app.services.taggun.schemas.taggun_models import (
    AddressSchema,
    LineItemSchema,
    TaggunExtractedInvoiceBasic,
)

# Alta precisión global (el redondeo a 2 decimales lo maneja quant2)
getcontext().prec = 38


# ========= Extractor =========
class TaggunExtractor:
    def __init__(self, payload: dict):
        if not isinstance(payload, dict):
            raise OCRPayloadFormatError(data={"received_type": type(payload).__name__})
        self.ocr_data = payload
        self.candidates: Set[Decimal] = set()
        self.corrected_values: Dict[str, Decimal] = {}
        self.line_items_total: Decimal = Decimal("0")

        # Tasas estándar como Decimal
        self._standard_rates: List[Decimal] = [
            D(r) for r in getattr(settings, "TAX_STANDARD_RATES", [])
        ]

        # Tolerancias
        self._rate_tolerance: Decimal = Decimal("0.30")  # tolerancia en puntos de %
        self._sum_tolerance: Decimal = Decimal("0.05")  # tolerancia en dinero

    # -----------------------
    # Utils
    # -----------------------
    @staticmethod
    def parse_iso_date(value: str):
        """Convierte '2024-01-01T00:00:00Z' a date o None."""
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
        # Mantengo compatibilidad con tu excepción existente
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

    def _valid_values(
        self,
        amount_total: Decimal,
        amount_tax: Decimal,
        amount_untaxed: Decimal,
        line_items: List[LineItemSchema] | bool,
        raise_on_mismatch: bool = False,
    ):
        EPS = self._sum_tolerance
        total_expected = quant2(D(amount_untaxed) or Decimal("0"))

        # Validación de self.line_items_total vs. amount_untaxed usando tolerancia monetaria
        if not line_items:
            return False

        if abs(self.line_items_total - total_expected) > EPS:
            if raise_on_mismatch:
                raise LineItemsSumMismatchError(
                    expected=total_expected,
                    obtained=quant2(self.line_items_total),
                    tolerance=EPS,
                )
            return False

        if round(abs(amount_total - (self.line_items_total + amount_tax)), 2) > EPS:
            if raise_on_mismatch:
                raise LineItemsSumMismatchError(
                    expected=total_expected,
                    obtained=quant2(self.line_items_total),
                    tolerance=EPS,
                )
            return False

        return True

    # -----------------------
    # Address
    # -----------------------
    def extract_address(self) -> AddressSchema:
        try:
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
        except Exception as exc:
            raise OCRPayloadFormatError(
                "Error al extraer dirección", data={"error": str(exc)}
            )

    # -----------------------
    # Line Items
    # -----------------------
    def extract_line_items(self) -> list:
        items = self._try_paths(["entities", "productLineItems"], default=[])
        if items is None:
            raise OCRPayloadFormatError("productLineItems es None")
        return items if isinstance(items, list) else []

    def parse_line_items(
        self,
    ) -> List[LineItemSchema]:
        """
        Devuelve ítems consistentes con el monto total global.
        - Si la suma no coincide con amount_untaxed, retorna False (por defecto)
          o lanza LineItemsSumMismatchError si raise_on_mismatch=True.
        """
        raw_items = self.extract_line_items()
        line_items: List[LineItemSchema] = []

        try:
            for item in raw_items:
                data = item.get("data", {}) or {}

                name = (data.get("name", {}) or {}).get("data", "") or ""
                _require(name, "line_item.name")

                # Quantity a Decimal para cálculo
                qty_raw = (data.get("quantity", {}) or {}).get("data", 0) or 0
                qty_dec = D(qty_raw, default="0")

                # Precios a Decimal para cálculo
                unit_price_dec = D(
                    (data.get("unitPrice", {}) or {}).get("data")
                ) or Decimal("0")

                # Calcular total de línea
                line_total_dec = unit_price_dec * qty_dec
                self.line_items_total += line_total_dec

                # Emitir float en el schema (redondeado a 2 decimales)
                line_items.append(
                    LineItemSchema(
                        name=name.strip(),
                        quantity=float(qty_dec),
                        unit_price=f2(unit_price_dec),
                        total_price=f2(line_total_dec),
                    )
                )
        except FieldNotFoundError:
            raise
        except Exception as exc:
            raise OCRPayloadFormatError(
                "Error al parsear ítems de línea", data={"error": str(exc)}
            )

        return line_items

    # -----------------------
    # Base values
    # -----------------------
    def extrac_base_values(self) -> TaggunExtractedInvoiceBasic:
        try:
            partner_name = self._try_paths(
                ["merchantName", "data"],
                ["entities", "merchantName", "data"],
            )
            partner_name = _require(partner_name, "partner_name")

            partner_vat = self._try_paths(
                ["merchantTaxId", "data"],
                ["entities", "merchantVerification", "data", "verificationId"],
            )
            partner_vat = (
                partner_vat or ""
            )  # tu schema lo requiere str; si no hay, vacío

            raw_date = self._try_paths(["date", "data"])
            date_invoice = self.parse_iso_date(raw_date)

            invoice_number = self._try_paths(
                ["invoiceNumber", "data"],
                ["entities", "invoiceNumber", "data"],
            )

            # Leer como Decimal y emitir como float
            amount_total_dec = D(self._try_paths(["totalAmount", "data"], default=0.0))
            amount_tax_dec = D(self._try_paths(["taxAmount", "data"], default=0.0))
            amount_untaxed_dec = D(self._try_paths(["paidAmount", "data"], default=0.0))
            amount_discount_dec = abs(
                D(self._try_paths(["discountAmount", "data"], default=0.0))
            )

            taggun_basic_fields = {
                "partner_name": partner_name,
                "partner_vat": partner_vat,
                "date": date_invoice,
                "invoice_number": invoice_number,
                "amount_total": f2(amount_total_dec),
                "amount_tax": f2(amount_tax_dec),
                "amount_untaxed": f2(amount_untaxed_dec),
                "amount_discount": f2(amount_discount_dec),
            }

            return TaggunExtractedInvoiceBasic(**taggun_basic_fields)

        except (FieldNotFoundError, MissingRequiredAmountsError):
            raise
        except Exception as exc:
            raise OCRPayloadFormatError(
                "Error al extraer campos base", data={"error": str(exc)}
            )

    # -----------------------
    # Tax candidates
    # -----------------------
    def calculate_tax_candidates(
        self,
        amount_untaxed: Decimal,
        amount_total: Decimal,
        amount_tax: Decimal,
        amount_discount: Optional[Decimal] = Decimal("0"),
    ) -> Set[float]:
        """
        Calcula candidatos de tasa de impuesto.
        ✅ Hace todos los cálculos en Decimal y retorna Set[float].
        """
        # Blindaje: trabajar con Decimal
        amount_untaxed = D(amount_untaxed)
        amount_total = D(amount_total)
        amount_tax = D(amount_tax)
        amount_discount = D(amount_discount)

        if not self._majority_gate(
            amount_tax=amount_tax,
            amount_total=amount_total,
            amount_untaxed=amount_untaxed,
        ):
            # Aprovechamos tu excepción composable
            raise MissingRequiredAmountsError(
                missing=[
                    k
                    for k, v in {
                        "amount_untaxed": amount_untaxed,
                        "amount_total": amount_total,
                        "amount_tax": amount_tax,
                    }.items()
                    if v <= 0
                ]
            )

        u, t, tx, d = (
            amount_untaxed or Decimal("0"),
            amount_total or Decimal("0"),
            amount_tax or Decimal("0"),
            amount_discount or Decimal("0"),
        )

        rate_tol = self._rate_tolerance
        sum_tol = self._sum_tolerance

        def is_valid_rate(untaxed: Decimal, tax: Decimal) -> bool:
            if untaxed <= 0:
                return False
            rate = quant2((tax / untaxed) * Decimal("100"))
            return any(abs(rate - r) <= rate_tol for r in self._standard_rates)

        try:
            # Caso 1: Descuento presente y todos los valores
            if d > 0 and u > 0 and tx > 0 and t > 0:
                expected_total = u - d + tx
                if abs(expected_total - t) > sum_tol:  # usar tolerancia de dinero
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
                return {float(c) for c in self.candidates}

            # Caso 2: Descuento presente, falta uno de los tres
            if d > 0:
                # Falta tax
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
                    return {float(c) for c in self.candidates}
                # Falta untaxed
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
                    return {float(c) for c in self.candidates}
                # Falta total
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
                    return {float(c) for c in self.candidates}

            # Caso 3: Sin descuento, todos los valores presentes
            if t > 0 and u > 0 and tx > 0:
                if abs((u + tx) - t) > sum_tol:  # usar tolerancia de dinero
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
                return {float(c) for c in self.candidates}

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

            return {float(c) for c in self.candidates}

        except (MissingRequiredAmountsError, TaxPercentageNotFound):
            raise
        except Exception as exc:
            raise OCRPayloadFormatError(
                "Error al calcular candidatos de impuesto", data={"error": str(exc)}
            )
