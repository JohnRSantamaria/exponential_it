from app.core.utils.tax_id_extractor import TaxIdExtractor
from app.services.openai.client import OpenAIService
from app.services.taggun.exceptions import AccountNotFoundError
from app.core.logging import logger
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice


def find_tax_ids(
    payload_text: str,
    all_tax_ids: list[str],
    taggun_data: TaggunExtractedInvoice,
) -> tuple[str, str, TaxIdExtractor]:
    extractor = TaxIdExtractor(
        text=payload_text,
        all_tax_ids=all_tax_ids,
    )

    logger.debug("Buscando un Tax ID válido para la compañía.")
    company_vat = extractor.get_company_tax_id_or_fail()
    logger.debug("Buscando un Tax ID válido para el proveedor.")
    partner_vat = extractor.get_partner_tax_id_or_fail(company_vat, taggun_data)

    return company_vat, partner_vat, extractor


def get_account_match(identify_accounts, company_vat: str, extractor: TaxIdExtractor):
    match = next(
        (
            a
            for a in identify_accounts.accounts
            if extractor._are_similar(a.account_tax_id, company_vat)
        ),
        None,
    )
    if not match:
        raise AccountNotFoundError(data={"vat": company_vat})
    return match
