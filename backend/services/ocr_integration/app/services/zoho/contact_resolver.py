from typing import List
from pydantic import TypeAdapter

from app.core.logger import configure_logging
from app.core.interface.account_provider import AccountingProvider

from app.services.ocr.schemas import Invoice, Supplier
from app.services.zoho.schemas.contact_response import ZohoContactResponse

from app.utils.comparator import are_similar

logger = configure_logging()


def extract_cifs(contact: ZohoContactResponse) -> List[str]:
    """Extrae todos los posibles CIF de un contacto."""
    cifs = []
    if contact.cf_cif:
        cifs.append(contact.cf_cif)
    for field in contact.custom_fields or []:
        if field.label == "CIF" and field.value:
            cifs.append(field.value)
    return cifs


async def get_or_create_partner_id(
    partner_vat: str | None, supplier: Supplier, provider: AccountingProvider
) -> str:
    """Busca un contacto por CIF o lo crea si no existe, retornando el partner_id."""

    # Obtener y parsear contactos
    raw_contacts = await provider.get_all_contacts()
    contacts: List[ZohoContactResponse] = TypeAdapter(
        List[ZohoContactResponse]
    ).validate_python(raw_contacts)

    logger.info(f"Buscando contacto con partner vat similar a: {partner_vat}")

    for contact in contacts:
        if any(are_similar(cif, partner_vat) for cif in extract_cifs(contact)):
            logger.info(
                f"Coincidencia encontrada: {contact.contact_name} ({contact.contact_id})"
            )
            return contact.contact_id

    logger.warning("No se encontró proveedor, creando nuevo contacto...")

    vendor_data = await provider.create_vendor(supplier)

    contact_id = vendor_data.get("contact_id")

    if not contact_id:
        raise ValueError("La respuesta del proveedor no contiene 'contact_id'.")
    return contact_id
