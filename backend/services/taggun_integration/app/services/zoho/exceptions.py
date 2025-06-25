from exponential_core.exceptions import CustomAppException


class ContactIdNotFoundError(CustomAppException):
    def __init__(self, message="No se pudo crear correctamente el contacto", data=None):
        super().__init__(message, data, status_code=422)


class ZohoServiceError(CustomAppException):
    def __init__(self, message="Error en la respuesta de Zoho", data=None):
        super().__init__(message=message, data=data, status_code=502)


class ZohoTimeoutError(ZohoServiceError):
    def __init__(self, message="Zoho no respondió a tiempo", data=None):
        super().__init__(message=message, data=data)


class ZohoConnectionError(ZohoServiceError):
    def __init__(self, message="No se pudo conectar con Zoho", data=None):
        super().__init__(message=message, data=data)


class ZohoUnexpectedError(ZohoServiceError):
    def __init__(self, message="Error inesperado al comunicarse con Zoho", data=None):
        super().__init__(message=message, data=data)
