from exponential_core.exceptions import CustomAppException


class FileProcessingError(CustomAppException):
    def __init__(self, message="No se pudo leer el archivo", data=None):
        super().__init__(message, data, status_code=422)


class AccountNotFoundError(CustomAppException):
    def __init__(
        self, message="No se encontraron cuentas asociadas al correo", data=None
    ):
        super().__init__(message, data, status_code=404)


class AdminServiceError(CustomAppException):
    def __init__(self, message="Error al comunicarse con el servicio Admin", data=None):
        super().__init__(message, data, status_code=503)


class FieldNotFoundError(CustomAppException):
    def __init__(self, field_name: str, message: str = None, data: dict = None):
        default_message = (
            f"No se encontró un valor valido para el campo requerido: '{field_name}'"
        )
        super().__init__(
            message=message or default_message,
            data={**(data or {}), "field": field_name},
            status_code=422,
        )
