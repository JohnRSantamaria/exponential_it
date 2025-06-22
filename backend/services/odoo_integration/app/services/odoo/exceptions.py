from exponential_core.exceptions import CustomAppException


class OdooSecretsNotFound(CustomAppException):
    def __init__(self, client_vat: str):
        super().__init__(
            message=f"No se encontraron secretos para el cliente '{client_vat}' en AWS Secrets Manager.",
            status_code=500,
            data={"client_vat": client_vat},
        )


class MissingSecretKey(CustomAppException):
    def __init__(self, client_vat: str, key: str):
        super().__init__(
            message=f"Falta la clave secreta '{key}' para el cliente '{client_vat}'.",
            status_code=500,
            data={"client_vat": client_vat, "missing_key": key},
        )
