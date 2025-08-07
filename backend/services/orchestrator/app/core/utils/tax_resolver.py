from typing import Set
from app.core.settings import settings
from app.services.zoho.exceptions import TaxPercentageNotFound
from app.core.logging import logger


class TaxCalculator:
    def __init__(
        self,
        amount_untaxed: float,
        amount_total: float,
        amount_tax: float,
        amount_discount: float,
    ):
        self.amount_untaxed = amount_untaxed
        self.amount_total = amount_total
        self.amount_tax = amount_tax
        self.amount_discount = amount_discount
        self.candidates: Set[float] = set()

    def majority_gate(self) -> bool:
        return (
            (self.amount_untaxed > 0) + (self.amount_total > 0) + (self.amount_tax > 0)
        ) >= 2

    @staticmethod
    def normalize(value: float, tolerance: float = 0.03) -> float:
        rounded = round(value, 2)
        for standard in settings.TAX_STANDARD_RATES:
            if abs(rounded - standard) <= tolerance:
                return standard
        return rounded

    def _add_candidate(self, percentage: float) -> None:
        normalized = self.normalize(percentage)
        if normalized in settings.TAX_STANDARD_RATES:
            self.candidates.add(normalized)

    def _compute_percentage(self, untaxed: float, tax: float) -> None:
        if untaxed <= 0:
            return
        percentage = (tax / untaxed) * 100
        self._add_candidate(percentage)

    def calculate(self) -> Set[float]:
        if not self.majority_gate():
            self._raise_error()

        u, t, tx, d = (
            self.amount_untaxed,
            self.amount_total,
            self.amount_tax,
            self.amount_discount,
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

        return self.candidates

    def _raise_error(self):
        raise TaxPercentageNotFound(
            data={
                "amount_untaxed": self.amount_untaxed,
                "amount_total": self.amount_total,
                "amount_tax": self.amount_tax,
                "amount_discount": self.amount_discount,
            }
        )
