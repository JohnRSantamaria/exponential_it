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
    percentages = []

    try:
        if amount_untaxed:
            percentages.append(round((amount_tax / amount_untaxed) * 100, 2))
            percentages.append(
                round(((amount_total - amount_untaxed) / amount_untaxed) * 100, 2)
            )
        if amount_total and amount_tax:
            amount_untaxed_est = amount_total - amount_tax
            if amount_untaxed_est:
                percentages.append(round((amount_tax / amount_untaxed_est) * 100, 2))
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
