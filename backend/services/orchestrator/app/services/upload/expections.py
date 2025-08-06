from exponential_core.exceptions import CustomAppException


class FileUploadError(CustomAppException):
    def __init__(self, message: str, data=None):
        super().__init__(message=message, data=data, status_code=422)


class DropboxServiceError(CustomAppException):
    def __init__(self, message="Error general con Dropbox", data=None):
        super().__init__(message, data=data, status_code=422)


class DropboxUploadError(DropboxServiceError):
    def __init__(self, path: str, detail: str = None):
        message = f"Error al subir archivo a Dropbox: {path}"
        super().__init__(message, data={"path": path, "detail": detail})


class DropboxFileExistsError(DropboxServiceError):
    def __init__(self, path: str):
        super().__init__(
            f"El archivo ya existe en Dropbox: {path}", data={"path": path}
        )


class DropboxConnectionError(DropboxServiceError):
    def __init__(self, detail: str = None):
        super().__init__("No se pudo conectar con Dropbox", data={"detail": detail})
