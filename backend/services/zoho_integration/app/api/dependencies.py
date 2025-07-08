from fastapi import Depends, Header


def get_client_vat(
    x_client_vat: str = Header(..., description="Identificador VAT/NIT del cliente")
) -> str:
    return x_client_vat


async def get_company(client_vat: str = Depends(get_client_vat)) -> str:
    """
    Actualmente solo retorna el VAT recibido por encabezado,
    pero se puede extender para cargar secretos, validar el cliente, etc.
    """
    return client_vat
