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
