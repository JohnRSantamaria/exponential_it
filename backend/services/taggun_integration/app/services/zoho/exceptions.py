from exponential_core.exceptions import CustomAppException


class ContactIdNotFoundError(CustomAppException):
    def __init__(self, message="No se pudo crear correctamente el contacto", data=None):
        super().__init__(message, data, status_code=422)
