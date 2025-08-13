from exponential_core.exceptions import CustomAppException


class FileProcessingError(CustomAppException):
    def __init__(self, message="No se pudo leer el archivo", data=None):
        super().__init__(message, data, status_code=422)


class AccountNotFoundError(CustomAppException):
    def __init__(
        self, message="No se encontraron cuentas asociadas a esta cuenta", data=None
    ):
        super().__init__(message, data, status_code=404)


class AdminServiceError(CustomAppException):
    def __init__(self, message="Error al comunicarse con el servicio Admin", data=None):
        super().__init__(message, data, status_code=401)


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


class ImageTooSmall(CustomAppException):
    def __init__(
        self,
        width: int,
        height: int,
        min_width: int = 100,
        min_height: int = 100,
        message: str = None,
        data: dict = None,
    ):
        default_message = (
            f"La imagen es demasiado pequeña: {width}x{height}. "
            f"Se requiere un mínimo de {min_width}x{min_height}."
        )
        super().__init__(
            message=message or default_message,
            data={
                **(data or {}),
                "width": width,
                "height": height,
                "min_width": min_width,
                "min_height": min_height,
            },
            status_code=422,
        )


class UnsupportedImageFormatError(CustomAppException):
    def __init__(
        self,
        file_type: str,
        supported_types: list[str] = None,
        message: str = None,
        data: dict = None,
    ):
        supported_types = supported_types or ["jpg", "jpeg", "png", "bmp", "tiff"]
        default_message = (
            f"Formato de imagen no soportado: '{file_type}'. "
            f"Formatos permitidos: {', '.join(supported_types)}."
        )
        super().__init__(
            message=message or default_message,
            data={
                **(data or {}),
                "file_type": file_type,
                "supported_types": supported_types,
            },
            status_code=415,  # 415 Unsupported Media Type
        )
