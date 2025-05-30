import json
from fastapi.exceptions import RequestValidationError


def valid_json(payload: str) -> dict:
    """
    Valida que el payload sea un JSON en formato objeto (dict).
    Lanza un RequestValidationError si es inválido.
    """
    try:
        parsed_payload = json.loads(payload)
        if not isinstance(parsed_payload, dict):
            raise ValueError()

        return parsed_payload

    except (json.JSONDecodeError, ValueError):
        raise RequestValidationError(
            "El campo 'payload' debe ser un JSON válido con formato de objeto (dict)."
        )
