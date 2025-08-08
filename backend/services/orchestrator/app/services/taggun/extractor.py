from datetime import datetime
from typing import Dict, Set

from app.core.settings import settings
from app.core.logging import logger
from app.services.zoho.exceptions import TaxPercentageNotFound
from app.services.taggun.schemas.taggun_models import (
    AddressSchema,
    LineItemSchema,
    TaggunExtractedInvoice,
)


class TaggunExtractor:
    def __init__(self, payload):
        self.ocr_data = payload
        self.candidates: Set[float] = set()
        self.corrected_values: Dict[str:float] = {}

    @staticmethod
    def safe_float(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_iso_date(value: str):
        """
        Intenta convertir una cadena ISO (como '2024-01-01T00:00:00Z') en un objeto `date`.
        Retorna None si no es válida.
        """
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except Exception:
            return None

    @staticmethod
    def normalize(value: float, tolerance: float = 0.03) -> float:
        rounded = round(value, 2)
        for standard in settings.TAX_STANDARD_RATES:
            if abs(rounded - standard) <= tolerance:
                return standard
        return rounded

    @staticmethod
    def _majority_gate(
        amount_untaxed: float, amount_total: float, amount_tax: float
    ) -> bool:
        return ((amount_untaxed > 0) + (amount_total > 0) + (amount_tax > 0)) >= 2

    def _raise_error(self):
        raise TaxPercentageNotFound()

    def _add_candidate(self, percentage: float) -> None:
        normalized = self.normalize(percentage)
        if normalized in settings.TAX_STANDARD_RATES:
            self.candidates.add(normalized)

    def _compute_percentage(self, untaxed: float, tax: float) -> None:
        if untaxed <= 0:
            return
        percentage = (tax / untaxed) * 100
        self._add_candidate(percentage)

    def _try_paths(self, *paths, default=""):
        for path in paths:
            value = self.ocr_data
            for key in path:
                try:
                    value = value[key]
                except (KeyError, TypeError):
                    value = None
                    break
            if value is not None:
                return value
        return default

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

    def extract_line_items(self) -> list:
        items = self._try_paths(["entities", "productLineItems"], default=[])
        return items if isinstance(items, list) else []

    def parse_line_items(self, amount_total, amount_untaxed) -> list[LineItemSchema]:
        raw_items = self.extract_line_items()
        parsed_items: list[LineItemSchema] = []

        total_units = 0
        total_price_sum = 0.0
        total_unit_price_sum = 0.0

        products_name = ""
        for item in raw_items:
            data = item.get("data", {})

            product_name = data.get("name", {}).get("data", "").strip()
            products_name += f"{product_name}, "
            quantity = data.get("quantity", {}).get("data", 0)
            unit_price = self.safe_float(data.get("unitPrice", {}).get("data"))
            total_price = self.safe_float(data.get("totalPrice", {}).get("data"))

            # Acumuladores
            total_units += quantity
            total_price_sum += total_price
            total_unit_price_sum += unit_price

            # Crear instancia del esquema y agregarla a la lista
            parsed_items.append(
                LineItemSchema(
                    name=product_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                )
            )

        if total_unit_price_sum > amount_untaxed or total_price_sum > amount_total:
            return [
                LineItemSchema(
                    name=products_name,
                    quantity=1,
                    unit_price=amount_untaxed,
                    total_price=amount_total,
                )
            ]
        return parsed_items

    def extract_data(self) -> TaggunExtractedInvoice:
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

        amount_total = self._try_paths(["totalAmount", "data"], default=0.0)
        amount_tax = self._try_paths(["taxAmount", "data"], default=0.0)
        amount_untaxed = self._try_paths(["paidAmount", "data"], default=0.0)
        amount_discount = self._try_paths(["discountAmount", "data"], default=0.0)

        tax_canditates = self.calculate_tax_candidates(
            amount_discount=amount_discount,
            amount_tax=amount_tax,
            amount_total=amount_total,
            amount_untaxed=amount_untaxed,
        )

        corrected = self.corrected_values

        if corrected:
            if amount_untaxed != corrected["amount_untaxed"]:
                logger.debug(
                    f"Corrigiendo amount_untaxed: {amount_untaxed} -> {corrected['amount_untaxed']}"
                )
                amount_untaxed = corrected["amount_untaxed"]
            if amount_total != corrected["amount_total"]:
                logger.debug(
                    f"Corrigiendo amount_total: {amount_total} -> {corrected['amount_total']}"
                )
                amount_total = corrected["amount_total"]
            if amount_tax != corrected["amount_tax"]:
                logger.debug(
                    f"Corrigiendo amount_tax: {amount_tax} -> {corrected['amount_tax']}"
                )
                amount_tax = corrected["amount_tax"]

        address = self.extract_address()
        lines = self.parse_line_items(
            amount_total=amount_total, amount_untaxed=amount_untaxed
        )

        return TaggunExtractedInvoice(
            partner_name=partner_name,
            partner_vat=partner_vat,
            date=date_invoice,
            invoice_number=invoice_number,
            amount_total=amount_total,
            amount_tax=amount_tax,
            amount_untaxed=amount_untaxed,
            amount_discount=amount_discount or 0,
            address=address,
            line_items=lines,
            tax_canditates=tax_canditates,
        )

    def calculate_tax_candidates(
        self,
        amount_untaxed: float,
        amount_total: float,
        amount_tax: float,
        amount_discount: float,
    ) -> Set[float]:

        if not self._majority_gate(
            amount_tax=amount_tax,
            amount_total=amount_total,
            amount_untaxed=amount_untaxed,
        ):
            self._raise_error()

        u, t, tx, d = (
            amount_untaxed,
            amount_total,
            amount_tax,
            amount_discount,
        )

        def is_valid_rate(untaxed: float, tax: float) -> bool:
            if untaxed <= 0:
                return False
            rate = round((tax / untaxed) * 100, 2)
            return any(abs(rate - r) <= 0.3 for r in settings.TAX_STANDARD_RATES)

        # Caso 1: Descuento presente y todos los valores
        if d > 0 and u > 0 and tx > 0 and t > 0:
            expected_total = u - d + tx
            if abs(expected_total - t) > 0.3:
                u2 = t - tx + d
                if is_valid_rate(u2, tx):
                    u = u2
                else:
                    self._raise_error()
            self._compute_percentage(u, tx)
            return self.candidates

        # Caso 2: Descuento presente, falta uno de los tres
        if d > 0:
            if t > 0 and u > 0 and tx <= 0:
                tx = t - (u - d)
                if not is_valid_rate(u, tx):
                    self._raise_error()
                self._compute_percentage(u, tx)
                return self.candidates

            elif t > 0 and tx > 0 and u <= 0:
                u = t - tx + d
                if not is_valid_rate(u, tx):
                    self._raise_error()
                self._compute_percentage(u, tx)
                return self.candidates

            elif u > 0 and tx > 0 and t <= 0:
                t = u - d + tx
                if not is_valid_rate(u, tx):
                    self._raise_error()
                self._compute_percentage(u, tx)
                return self.candidates

        # Caso 3: Sin descuento, todos los valores presentes
        if t > 0 and u > 0 and tx > 0:
            if abs(u + tx - t) > 0.3:
                expected_untaxed = t - tx
                expected_total = u + tx

                rate_if_untaxed_fixed = (
                    (tx / expected_untaxed) * 100 if expected_untaxed > 0 else -1
                )
                rate_if_total_fixed = (tx / u) * 100 if u > 0 else -1

                match_untaxed = any(
                    abs(rate_if_untaxed_fixed - r) <= 0.3
                    for r in settings.TAX_STANDARD_RATES
                )
                match_total = any(
                    abs(rate_if_total_fixed - r) <= 0.3
                    for r in settings.TAX_STANDARD_RATES
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
                "amount_untaxed": u,
                "amount_total": t,
                "amount_tax": tx,
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
            "amount_untaxed": u,
            "amount_total": t,
            "amount_tax": tx,
        }

        return self.candidates
