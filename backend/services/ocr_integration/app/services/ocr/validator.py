import json
from fastapi.exceptions import RequestValidationError


def valid_json(payload: str) -> dict:
    """
    Valida que el payload sea un JSON en formato objeto (dict).
    Lanza un RequestValidationError si es inválido.
    """
    try:
        ocr_data = json.loads(payload)
        if not isinstance(ocr_data, dict):
            raise ValueError()

        return ocr_data

    except (json.JSONDecodeError, ValueError):
        raise RequestValidationError(
            "El campo 'payload' debe ser un JSON válido con formato de objeto (dict)."
        )
