# app/core/types.py


class CustomAppException(Exception):
    def __init__(self, message: str, data: dict = None, status_code: int = 400):
        self.message = message
        self.data = data or {}
        self.status_code = status_code
