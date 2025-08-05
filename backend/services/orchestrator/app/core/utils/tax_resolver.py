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

    def reorder(
        self,
        amount_untaxed: float,
        amount_total: float,
        amount_tax: float,
        amount_discount: float | None = None,
    ):
        """What if exist an discound"""
        if amount_discount > 0 or amount_discount:
            logger.warning("Se dectecto un descuento en la factura.")
            amount_total = amount_untaxed + amount_tax

        """Reorder amounts to ensure total ≥ untaxed ≥ tax."""
        if amount_total <= 0 and amount_untaxed <= 0 and amount_tax <= 0:
            raise TaxPercentageNotFound(
                data={
                    "amount_untaxed": amount_untaxed,
                    "amount_total": amount_total,
                    "amount_tax": amount_tax,
                    "amount_discount": self.amount_discount,
                }
            )

        # what if due to an error we similar values in total, untaxed, and tax?
        if amount_total == amount_untaxed == amount_tax:
            raise TaxPercentageNotFound(
                data={
                    "amount_untaxed": amount_untaxed,
                    "amount_total": amount_total,
                    "amount_tax": amount_tax,
                    "amount_discount": self.amount_discount,
                }
            )

        if amount_total == amount_untaxed and amount_tax > 0:
            percentage = (amount_tax / amount_untaxed) * 100
            normalized = self.normalize(percentage)

            if normalized in settings.TAX_STANDARD_RATES:
                self.amount_total = amount_untaxed + amount_tax
                amount_total = amount_untaxed + amount_tax
            else:
                self.amount_untaxed = amount_total - amount_tax
                amount_untaxed = amount_total - amount_tax

        if amount_untaxed > 0 and amount_total > 0 and amount_tax > 0:  # 1 1 1 => 1
            values = [amount_untaxed, amount_total, amount_tax]
            values.sort(reverse=True)  # Ordena de mayor a menor
            self.amount_untaxed = values[1]
            self.amount_total = values[0]
            self.amount_tax = values[2]

        elif amount_total <= 0 and amount_tax > 0 and amount_untaxed > 0:  # 0 1 1 => 1
            values = [amount_tax, amount_untaxed]
            values.sort(reverse=True)  # Ordena de mayor a menor
            self.amount_tax = values[1]
            self.amount_untaxed = values[0]

            self.amount_total = self.amount_untaxed + self.amount_tax

        elif amount_total > 0 and amount_untaxed <= 0 and amount_tax > 0:  # 1 0 1 => 1
            values = [amount_total, amount_tax]
            values.sort(reverse=True)  # Ordena de mayor a menor
            self.amount_total = values[0]
            self.amount_tax = values[1]
            self.amount_untaxed = self.amount_total - self.amount_tax
        elif amount_total > 0 and amount_untaxed > 0 and amount_tax <= 0:  # 1 1 0 => 1
            values = [amount_total, amount_untaxed]
            values.sort(reverse=True)  # Ordena de mayor a menor
            self.amount_total = values[0]
            self.amount_untaxed = values[1]
            self.amount_tax = self.amount_total - self.amount_untaxed
        elif amount_total > 0 and amount_untaxed <= 0 and amount_tax <= 0:
            self.amount_untaxed = amount_total
            self.amount_tax = 0.0
        else:
            raise TaxPercentageNotFound(
                data={
                    "amount_untaxed": amount_untaxed,
                    "amount_total": amount_total,
                    "amount_tax": amount_tax,
                    "amount_discount": self.amount_discount,
                }
            )

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
