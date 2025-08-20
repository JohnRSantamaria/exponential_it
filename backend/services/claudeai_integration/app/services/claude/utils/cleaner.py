from exponential_core.cluadeai import InvoiceResponseSchema
from pydantic import ValidationError


def _clean_possible_markdown(json_text: str) -> str:
    """
    Removes ```json ... ``` wrappers if present and trims whitespace.
    """
    clean = json_text.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    if clean.startswith("```"):  # in case of ``` without language
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    return clean.strip()


def parse_invoice_response_from_json(json_text: str) -> InvoiceResponseSchema:
    """
    Validates the JSON returned by Claude and converts it to English models.
    """
    clean = _clean_possible_markdown(json_text)
    try:
        return InvoiceResponseSchema.model_validate_json(clean)
    except ValidationError as ve:
        raise ve
