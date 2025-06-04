# app/core/types.py
class CustomAppException(Exception):
    def __init__(self, message: str, data: dict = None, status_code: int = 400):
        self.message = message
        self.data = data or {}
        self.status_code = status_code


class InvoiceParsingError(CustomAppException):
    def __init__(self, detail: str):
        super().__init__(f"Error al parsear factura: {detail}", status_code=422)


class TaxIdNotFoundError(CustomAppException):
    def __init__(self, invoice_number: str, candidates: list[float]):
        super().__init__(
            message=(
                f"No se encontró un tax_id válido para la factura '{invoice_number}'. "
                f"Porcentajes candidatos: {candidates}"
            ),
            status_code=422,
            data={
                "invoice_number": invoice_number,
                "candidates": candidates,
            },
        )
