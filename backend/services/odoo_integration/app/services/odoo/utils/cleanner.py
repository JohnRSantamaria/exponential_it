from enum import Enum
from datetime import datetime


def clean_enum_payload(data: dict) -> dict:
    """
    Recorre un diccionario y convierte cualquier valor Enum a su representación .value.
    """
    return {
        key: value.value if isinstance(value, Enum) else value
        for key, value in data.items()
    }


def parse_to_date(value):
    if isinstance(value, datetime):
        return value.date()
    elif isinstance(value, str):
        return datetime.fromisoformat(value).date()
    return value
