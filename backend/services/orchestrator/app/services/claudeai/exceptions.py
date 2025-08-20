from exponential_core.exceptions import CustomAppException


class ExtractionCladeError(CustomAppException):
    def __init__(self, detail: str):
        super().__init__(f"Error al parsear factura: {detail}", status_code=422)
