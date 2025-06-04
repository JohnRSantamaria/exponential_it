import difflib
from typing import List
from pydantic import TypeAdapter

from app.core.enums import ServicesEnum
from app.core.adapter.base import get_provider
from app.core.interface.account_provider import AccountingProvider
from app.core.logger import configure_logging
from app.services.ocr.schemas import Invoice, Supplier
from app.services.zoho.schemas.responses import ZohoContact

logger = configure_logging()


def are_similar(a: str, b: str, threshold: float = 0.9) -> bool:
    """Compara dos strings y retorna True si son al menos `threshold` similares."""
    if not a or not b:
        return False
    return (
        difflib.SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()
        >= threshold
    )


def extract_cifs(contact: ZohoContact) -> List[str]:
    """Extrae todos los posibles CIF de un contacto."""
    cifs = []
    if contact.cf_cif:
        cifs.append(contact.cf_cif)
    for field in contact.custom_fields or []:
        if field.label == "CIF" and field.value:
            cifs.append(field.value)
    return cifs


async def get_or_create_contact_id(
    invoice: Invoice, supplier: Supplier, provider: AccountingProvider
) -> str:
    """Busca un contacto por CIF o lo crea si no existe, retornando el contact_id."""

    # Obtener y parsear contactos
    raw_contacts = await provider.get_all_contacts()
    contacts: List[ZohoContact] = TypeAdapter(List[ZohoContact]).validate_python(
        raw_contacts
    )

    invoice_cif = invoice.partner_vat
    logger.info(f"Buscando contacto con CIF similar a: {invoice_cif}")

    for contact in contacts:
        if any(are_similar(cif, invoice_cif) for cif in extract_cifs(contact)):
            logger.info(
                f"Coincidencia encontrada: {contact.contact_name} ({contact.contact_id})"
            )
            return contact.contact_id

    logger.warning("No se encontró proveedor, creando nuevo contacto...")

    vendor_data = await provider.create_vendor(supplier)
    new_contact = ZohoContact(**vendor_data)
    logger.info(
        f"Contacto creado: {new_contact.contact_name} ({new_contact.contact_id})"
    )
    return new_contact.contact_id
