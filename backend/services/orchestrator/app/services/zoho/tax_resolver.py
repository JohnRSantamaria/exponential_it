from typing import Set, Tuple
from app.services.zoho.exceptions import TaxPercentageNotFound

TAX_STANDARD_RATES = (0.0, 4.0, 10.0, 21.0)


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
        for standard in TAX_STANDARD_RATES:
            if abs(rounded - standard) <= tolerance:
                return standard
        return rounded

    @staticmethod
    def reorder(a: float, b: float, c: float) -> Tuple[float, float, float]:
        values = [a, b, c]
        values.sort(reverse=True)
        return values[1], values[0], values[2]  # untaxed, total, tax

    def _add_candidate(self, percentage: float) -> None:
        normalized = self.normalize(percentage)
        if normalized in TAX_STANDARD_RATES:
            self.candidates.add(normalized)

    def _compute_percentage(self, untaxed: float, tax: float) -> None:
        if untaxed <= 0:
            return
        percentage = (tax / untaxed) * 100
        self._add_candidate(percentage)

    def calculate(self) -> Set[float]:
        if not self.majority_gate():
            self._raise_error()

        # Reordenar: garantiza que total ≥ untaxed ≥ tax
        self.amount_untaxed, self.amount_total, self.amount_tax = self.reorder(
            self.amount_untaxed, self.amount_total, self.amount_tax
        )

        u, t, tx = self.amount_untaxed, self.amount_total, self.amount_tax

        if t > 0 and u > 0 and tx > 0:
            if abs(u + tx - t) > 0.3:
                self._raise_error()
            self._compute_percentage(u, tx)

        elif t > 0 and u > 0 and tx <= 0:
            tx = t - u
            self._compute_percentage(u, tx)

        elif t > 0 and u <= 0 and tx > 0:
            u = t - tx
            self._compute_percentage(u, tx)

        elif t <= 0 and u > 0 and tx > 0:
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
