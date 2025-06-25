from exponential_core.exceptions import CustomAppException


class FileUploadError(CustomAppException):
    def __init__(self, message: str, data=None):
        super().__init__(message=message, data=data, status_code=502)
