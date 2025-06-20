from typing import List, Tuple

from app.core.utils.fiscal_id_extractor import FiscalIdExtractor
from app.core.utils.tax_id_validator import TaxIdValidator
from iso3166 import countries
from exponential_core.exceptions import ValidTaxIdNotFoundError


def is_valid_vat_country_code(vat_id: str) -> bool:
    if not vat_id or len(vat_id) < 2:
        return False
    prefix = vat_id[:2].upper()
    return prefix in countries


def filter_valid_tax_ids(candidates: List[Tuple[str, str]]) -> List[str]:
    """
    Filtra los identificadores fiscales válidos.
    """
    valid = []

    for tipo, valor in candidates:
        if tipo == "vat":
            if is_valid_vat_country_code(valor):
                valid.append(valor)
        else:

            valid.append(valor)

    return valid


def extract_supplier_tax_id(ocr_data: dict, cif: str) -> str:
    """
    Extrae la identificación fiscal del proveedor desde un payload OCR.
    """
    validator = TaxIdValidator(expected_cif=cif)
    text = validator.extract_text_from_payload(ocr_data)

    extractor = FiscalIdExtractor()
    found_ids = extractor.extract_all_ids(text)

    valid_ids = filter_valid_tax_ids(found_ids)

    if not valid_ids:
        raise ValidTaxIdNotFoundError(raw_ids=valid_ids)

    return validator.get_supplier_tax_id(valid_ids)
