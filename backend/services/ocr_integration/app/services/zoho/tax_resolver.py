from typing import List

from pydantic import TypeAdapter

from app.core.interface.account_provider import AccountingProvider
from app.core.logger import configure_logging
from app.services.ocr.schemas import Invoice
from app.services.zoho.schemas.tax_response import ZohoTaxResponse
from app.core.exceptions.types import TaxIdNotFoundError

logger = configure_logging()


def calculate_tax_percentage_candidates(
    amount_untaxed: float, amount_total: float, amount_tax: float
) -> set:
    TAX_STANDARD_RATES = [0.0, 4.0, 10.0, 21.0]

    def normalize(value: float, tolerance: float = 0.03) -> float:
        """
        Redondea a una tasa estándar si está dentro del margen de tolerancia,
        de lo contrario mantiene el valor con dos decimales.
        """
        rounded = round(value, 2)
        for standard in TAX_STANDARD_RATES:
            if abs(rounded - standard) <= tolerance:
                return standard
        return rounded

    percentages = []

    try:
        if amount_untaxed:
            percentages.append(normalize((amount_tax / amount_untaxed) * 100))
            percentages.append(
                normalize(((amount_total - amount_untaxed) / amount_untaxed) * 100)
            )
        if amount_total and amount_tax:
            amount_untaxed_est = amount_total - amount_tax
            if amount_untaxed_est:
                percentages.append(normalize((amount_tax / amount_untaxed_est) * 100))
    except ZeroDivisionError:
        pass

    return set(percentages)


async def get_tax_id(invoice: Invoice, provider: AccountingProvider) -> str:
    """Optiene tax_id y tax_percentage"""
    raw_taxes = await provider.get_all_taxes()
    taxes: List[ZohoTaxResponse] = TypeAdapter(List[ZohoTaxResponse]).validate_python(
        raw_taxes
    )

    candidate_set = calculate_tax_percentage_candidates(
        amount_untaxed=invoice.amount_untaxed,
        amount_total=invoice.amount_total,
        amount_tax=invoice.amount_tax,
    )
    candidates = list(candidate_set)

    matching_tax = next(
        (tax for tax in taxes if tax.tax_percentage in candidate_set), None
    )

    if matching_tax:
        for line in invoice.invoice_lines:
            line.tax_id = matching_tax.tax_id
            line.tax_percentage = matching_tax.tax_percentage
        return

    msg = (
        f"No se encontró un tax_id para el porcentaje de impuestos "
        f"{invoice.amount_tax} en la factura '{invoice.invoice_origin}'. "
        f"Candidatos generados: {candidates}"
    )
    logger.warning(f"[TAX_ID] CustomAppException: {msg}")
    raise TaxIdNotFoundError(invoice.invoice_origin, candidates)
