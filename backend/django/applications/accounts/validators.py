import re
from django.core.exceptions import ValidationError


def validate_tax_id(value):
    patterns = {
        "CIF": r"^[A-HJNPQRSUVW]\d{7}[0-9A-J]$",
        "NIF": r"^\d{8}[A-Z]$",
        "NIE": r"^[XYZ]\d{7}[A-Z]$",
        "VAT": r"^[A-Z]{2}[A-Z0-9]{8,12}$",
        "RFC": r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$",
        "CUIT": r"^\d{2}-\d{8}-\d$",
        "GENERIC": r"^[A-Z0-9\-\_\.]{5,20}$",
    }

    if not any(
        re.match(pattern, value, re.IGNORECASE) for pattern in patterns.values()
    ):
        raise ValidationError(f'El identificador fiscal "{value}" no es válido.')
