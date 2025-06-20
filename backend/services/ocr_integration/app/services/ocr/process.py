from typing import Annotated
from fastapi import File, UploadFile

from app.core.logging import logger
from app.core.settings import settings
from app.core.enums import UploadersEnum

from app.services.admin.client import AdminService
from app.services.admin.schemas import UserDataSchema
from app.services.ocr.extractor import CredentialExtractor
from app.services.ocr.parser_ocr import parser_invoice, parser_supplier
from app.core.utils.supplier_tax_id import extract_supplier_tax_id
from app.services.taggun.client import send_file_to_taggun
from app.services.upload.process import save_file
from app.services.zoho.process import zoho_process


async def optical_character_recognition(
    file: Annotated[UploadFile, File(...)],
    user_data: UserDataSchema,
    admin_service: AdminService,
):

    # 🔐 Obtener credenciales
    logger.debug("🔐 Obteniendo credenciales")
    service_credentials = await admin_service.service_credentials(
        service_id=settings.SERVICE_ID
    )
    extractor = CredentialExtractor(credentials=service_credentials)
    creds = extractor.extract_required_credentials()

    client_cif = creds.cif
    taggun_apikey = creds.taggun
    processor = creds.processor
    storage = creds.storage

    # 🧾 Leer contenido del archivo
    logger.info("🧾 Leer contenido del archivo")
    file_content = await file.read()

    # 📤 Enviar a Taggun
    logger.info("📤 Enviar a Taggun")
    ocr_data = await send_file_to_taggun(
        file_name=file.filename,
        file_content=file_content,
        content_type=file.content_type,
        api_key=taggun_apikey,
    )

    await admin_service.register_scan(user_id=user_data.user_id)
    logger.info("🟢 Escaneo registrado correctamente")

    # 🧠 Parsear datos relevantes
    invoice = parser_invoice(cif=client_cif, ocr_data=ocr_data)
    supplier = parser_supplier(cif=client_cif, ocr_data=ocr_data)
    partner_vat = extract_supplier_tax_id(ocr_data=ocr_data, cif=client_cif)

    invoice.partner_vat = partner_vat
    supplier.vat = partner_vat

    # 💼 Procesar en Zoho
    await zoho_process(
        invoice=invoice,
        supplier=supplier,
        file=file,
        file_content=file_content,
    )

    # 💾 Guardar archivo en Dropbox
    await save_file(
        invoice=invoice,
        file_content=file_content,
        file=file,
        uploader_name=UploadersEnum.DROPBOX,
    )
