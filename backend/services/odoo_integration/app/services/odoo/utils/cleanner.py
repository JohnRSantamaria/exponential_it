from enum import Enum


def clean_enum_payload(data: dict) -> dict:
    """
    Recorre un diccionario y convierte cualquier valor Enum a su representación .value.
    """
    return {
        key: value.value if isinstance(value, Enum) else value
        for key, value in data.items()
    }
