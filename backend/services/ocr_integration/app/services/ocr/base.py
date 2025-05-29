import json
from typing import Annotated

from fastapi import File, UploadFile
from fastapi.exceptions import RequestValidationError

from app.core.types import CustomAppException
from app.services.ocr.extractors import InvoiceExtractor


async def proces_document(payload: dict, file: Annotated[UploadFile, File(...)]):

    try:
        parsed_payload = json.loads(payload)
        if not isinstance(parsed_payload, dict):
            raise ValueError()
    except (json.JSONDecodeError, ValueError):
        raise RequestValidationError(
            "El campo 'payload' debe ser un JSON válido con formato de objeto (dict)."
        )

    extractor = InvoiceExtractor(json_data=parsed_payload)
    main_fields = extractor.extract_main_fields()

    return main_fields
