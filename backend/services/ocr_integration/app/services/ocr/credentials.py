from typing import List
from app.core.exceptions import CustomAppException
from app.services.admin.schemas import CredentialOut


def get_credential(credentials: List[CredentialOut], key: str):
    normalized_key = key.lower().strip()
    cred = next(
        (c for c in credentials if (c.key or "").lower().strip() == normalized_key),
        None,
    )

    if cred is None:
        raise CustomAppException(
            status_code=404, message=f'No se encontró la credencial con clave "{key}".'
        )

    return cred
