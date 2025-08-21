import json
from fastapi import UploadFile
from pydantic import BaseModel, ValidationError
from app.services.claudeai.client import ClaudeAIService
from app.core.logging import logger
from app.services.claudeai.extract_line_items import _truncate
from app.services.taggun.exceptions import AdminServiceError, FileProcessingError
from exponential_core.cluadeai import RetentionHTTPResponse


async def extract_withholdings_data(
    file: UploadFile,
    file_content: bytes,
    claudeai_service: ClaudeAIService,
):
    logger.info(
        "Comienza el proceso de obtención de retenciones a través de Claude AI."
    )

    try:
        response = await claudeai_service.extract_withholdings(
            file=file, file_content=file_content
        )
    except Exception as exc:
        # Errores de red / tiempo / etc. del cliente
        raise AdminServiceError(
            message="Error al comunicarse con el servicio Claude",
            data={"error": str(exc)},
        )

    # Normaliza a dict
    try:
        if isinstance(response, BaseModel):
            payload = response.model_dump()  # ✅ dict
        elif isinstance(response, dict):
            payload = response
        elif isinstance(response, str):
            payload = json.loads(response)  # ✅ parsea JSON string → dict
        elif hasattr(response, "json") and callable(getattr(response, "json")):
            payload = response.json()  # httpx.Response o similar
        else:
            raise AdminServiceError(
                message="Tipo de respuesta no soportado desde Claude",
                data={"type": type(response).__name__},
            )
    except Exception as exc:
        raise FileProcessingError(
            message="No se pudo parsear la respuesta de Claude",
            data={"error": str(exc), "response_preview": _truncate(response)},
        )

    # Valida con Pydantic v2
    try:
        # Recomendado en v2 en lugar de **payload
        return RetentionHTTPResponse.model_validate(payload)
        # (alternativa equivalente si prefieres kwargs y estás seguro de que es dict:)
        # return InvoiceResponseSchema(**payload)
    except ValidationError as ve:
        # Log útil y error claro hacia arriba
        logger.error(
            "❌ Error al validar JSON contra InvoiceResponseSchema: %s",
            _truncate(payload),
        )
        raise FileProcessingError(
            message="La respuesta de Claude no valida contra el esquema esperado",
            data={"errors": ve.errors(), "payload_preview": _truncate(payload)},
        )
