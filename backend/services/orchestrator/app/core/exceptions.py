from exponential_core.exceptions.base import CustomAppException


class TaxIdNotFoundError(CustomAppException):
    def __init__(self):
        super().__init__(
            message="No se encontró ningún identificador fiscal válido que coincida con los registrados.",
            status_code=422,
        )


class MultipleCompanyTaxIdMatchesError(CustomAppException):
    def __init__(self, matches: list[str]):
        super().__init__(
            message="Se encontraron múltiples coincidencias de identificadores fiscales con los registrados.",
            data={"matches": matches},
            status_code=422,
        )


class PartnerTaxIdNotFoundError(CustomAppException):
    def __init__(self):
        super().__init__(
            message="No se encontró identificador fiscal del proveedor.",
            status_code=422,
        )


class MultiplePartnerTaxIdsError(CustomAppException):
    def __init__(self, candidates: list[str]):
        super().__init__(
            message="Se encontraron múltiples identificadores fiscales de proveedor diferentes.",
            data={"candidates": candidates},
            status_code=422,
        )
