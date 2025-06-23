from typing import Annotated
from fastapi import File, UploadFile

from app.core.logging import logger
from app.core.settings import settings
from app.core.enums import UploadersEnum
from app.core.utils.supplier_tax_id import extract_supplier_tax_id

from app.services.admin.client import AdminService
from app.services.admin.schemas import UserDataSchema
from app.services.ocr.extractor import CredentialExtractor
from app.services.ocr.parser_ocr import parser_invoice, parser_supplier
from app.services.ocr.schemas import Invoice, Supplier
from app.services.odoo.process import odoo_process
from app.services.taggun.client import send_file_to_taggun
from app.services.upload.process import save_file
from app.services.zoho.process import zoho_process

from exponential_core.exceptions import CustomAppException


def parse_ocr_data(ocr_data: dict, client_cif: str) -> tuple[Invoice, Supplier]:
    invoice = parser_invoice(cif=client_cif, ocr_data=ocr_data)
    supplier = parser_supplier(cif=client_cif, ocr_data=ocr_data)
    partner_vat = extract_supplier_tax_id(ocr_data=ocr_data, cif=client_cif)

    if not partner_vat:
        logger.warning("No se encontró VAT del proveedor en los datos OCR")
        raise CustomAppException("No se pudo extraer el VAT del proveedor")

    invoice.partner_vat = partner_vat
    supplier.vat = partner_vat

    return invoice, supplier


async def optical_character_recognition(
    file: Annotated[UploadFile, File(...)],
    user_data: UserDataSchema,
    admin_service: AdminService,
):
    logger.debug("🔐 Obteniendo credenciales del servicio Admin")
    service_credentials = await admin_service.service_credentials(
        service_id=settings.SERVICE_ID
    )

    extractor = CredentialExtractor(credentials=service_credentials)
    creds = extractor.extract_required_credentials()

    client_vat = creds.cif
    processor = creds.processor
    storage = creds.storage

    taggun_api_key = settings.TAGGUN_APIKEY

    logger.debug("📄 Leyendo archivo subido")
    file_content = await file.read()
    if not file_content:
        raise CustomAppException("El archivo subido está vacío.")

    logger.debug("📤 Enviando archivo a Taggun para OCR")
    try:
        ocr_data = await send_file_to_taggun(
            file_name=file.filename,
            file_content=file_content,
            content_type=file.content_type,
            api_key=taggun_api_key,
        )
        if not ocr_data:
            raise CustomAppException("Respuesta vacía de Taggun")
    except Exception as e:
        logger.warning("❌ Error durante el procesamiento OCR con Taggun")
        raise CustomAppException(f"OCR fallido: {e}")

    logger.debug("✅ Registrando escaneo en Admin")
    await admin_service.register_scan(user_id=user_data.user_id)

    logger.debug("🧠 Parseando datos OCR")
    invoice, supplier = parse_ocr_data(ocr_data=ocr_data, client_cif=client_vat)

    logger.debug(
        f"📦 Procesando factura para proveedor {supplier.vat} y cliente {client_vat}"
    )

    if processor == "zoho":
        await zoho_process(
            invoice=invoice,
            supplier=supplier,
            file=file,
            file_content=file_content,
        )
    else:
        await odoo_process(invoice=invoice, supplier=supplier)

    return
    """TODO : falta pasar los parametros desde AWS para que funcione, es decir debo enviar 
                tambien el client_vat.  
    """
    if storage == "dropbox":
        await save_file(
            invoice=invoice,
            file_content=file_content,
            file=file,
            uploader_name=UploadersEnum.DROPBOX,
        )
