from exponential_core.exceptions import CustomAppException


class OdooCallException(CustomAppException):
    """
    Excepción personalizada para errores en llamadas a Odoo vía JSON-RPC.
    """

    def __init__(self, message: str, odoo_error: dict = None, status_code: int = 502):
        super().__init__(
            message=message, data=odoo_error or {}, status_code=status_code
        )
