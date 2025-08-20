from decimal import Decimal, ROUND_HALF_UP
from typing import List
from fastapi import UploadFile

from app.services.claudeai.client import ClaudeAIService
from app.services.claudeai.exceptions import ExtractionCladeError
from app.services.taggun.schemas.taggun_models import LineItemSchema
from app.core.logging import logger


def _to_decimal(value) -> Decimal:
    """Convertir cualquier valor (str, float, Decimal) a Decimal de forma segura."""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def line_items_extraction(
    file: UploadFile,
    file_content: bytes,
    claudeai_service: ClaudeAIService,
    amount_total: Decimal | float,
    amount_untaxed: Decimal | float,
) -> List[LineItemSchema]:
    logger.info("Comienza el proceso de obtención de ítems a través de Claude AI.")

    invoice_response = await claudeai_service.extract_claude_invoce(
        file=file, file_content=file_content
    )

    parsed_items: List[LineItemSchema] = []
    items = invoice_response.items

    # Normalizamos valores
    amount_total = _to_decimal(amount_total)
    amount_untaxed = _to_decimal(amount_untaxed)

    # Sumamos totales de los ítems
    lines_total = Decimal("0.00")
    for item in items:
        line_total = _to_decimal(item.line_total)
        lines_total += line_total

        parsed_items.append(
            LineItemSchema(
                name=item.description,
                quantity=_to_decimal(item.quantity),
                unit_price=_to_decimal(item.unit_price),
                total_price=line_total,
            )
        )

    # Validaciones
    if lines_total != amount_untaxed:
        raise ExtractionCladeError(
            detail=f"La suma de los ítems ({lines_total}) no coincide con el total sin impuestos ({amount_untaxed})."
        )

    if amount_total < amount_untaxed:
        raise ExtractionCladeError(
            detail=f"El total con impuestos ({amount_total}) es menor que el subtotal ({amount_untaxed}), lo cual es inconsistente."
        )

    logger.info(
        f"✅ Validación correcta: Subtotal ítems={lines_total}, Subtotal esperado={amount_untaxed}, "
        f"Total factura={amount_total}"
    )
    return parsed_items
