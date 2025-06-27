from exponential_core.exceptions import CustomAppException


class OdooServiceError(CustomAppException):
    def __init__(self, message="Error en la respuesta de Odoo", data=None):
        super().__init__(message=message, data=data, status_code=502)


class OdooTimeoutError(OdooServiceError):
    def __init__(self, message="Odoo no respondió a tiempo", data=None):
        super().__init__(message=message, data=data)


class OdooConnectionError(OdooServiceError):
    def __init__(
        self,
        message="[Error de conexión] No se pudo conectar con el microservicio : Odoo",
        data=None,
    ):
        super().__init__(message=message, data=data)


class OdooUnexpectedError(OdooServiceError):
    def __init__(self, message="Error inesperado al comunicarse con Odoo", data=None):
        super().__init__(message=message, data=data)
