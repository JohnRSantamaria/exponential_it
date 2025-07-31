import asyncio
from fastapi import UploadFile
from app.services.odoo.v16.processor import odoo_process as odoo_process_v16
from app.services.odoo.v18.processor import odoo_process as odoo_process_v18
from app.services.taggun.utils.valid_size import validate_image_dimensions
from app.services.upload.process import save_file_dropbox
from app.services.zoho.processor import zoho_process
from .ocr import extract_ocr_payload, extract_taggun_data
from .account_lookup import get_accounts_by_email
from .tax_id_matching import find_tax_ids, get_account_match
from .register import register_scan
from app.core.logging import logger
from app.core.secrets import SecretsService


async def handle_invoice_scan(
    recipient: str, file: UploadFile, file_content: bytes | None = None
):
    file_content = file_content or await file.read()
    logger.info(f"Inicia el Extraccion de {file.filename} para : {recipient}")

    validate_image_dimensions(file.filename, file_content)

    accounts_response = await get_accounts_by_email(email=recipient)
    all_tax_ids = [a.account_tax_id for a in accounts_response.accounts]

    payload = await extract_ocr_payload(file=file, file_content=file_content)
    logger.info("Comienzo de extracción de datos OCR")
    taggun_data = extract_taggun_data(payload)

    payload_text = payload.get("text", {}).get("text", "")
    company_vat, partner_vat, extractor = find_tax_ids(payload_text, all_tax_ids)
    taggun_data.partner_vat = partner_vat
    account = get_account_match(accounts_response, company_vat, extractor)

    await register_scan(
        user_id=accounts_response.user_id,
        account_id=account.account_id,
    )
    logger.info(
        f"Registro de escaneo completado para {account.account_name} - {account.account_tax_id} "
    )

    secrets_service = await SecretsService(company_vat=company_vat).load()
    invoice_processor = secrets_service.get_invoice_processor()

    if invoice_processor == "ZOHO":
        logger.info(f"Inicia el proceso de Zoho")
        await zoho_process(
            file=file,
            file_content=file_content,
            taggun_data=taggun_data,
            company_vat=company_vat,
        )
    elif invoice_processor == "ODOO":
        odoo_version = secrets_service.get_odoo_version()
        logger.info(f"Inicia el proceso de Odoo versión : {odoo_version}")
        if odoo_version == "V16":
            await odoo_process_v16(
                file=file,
                file_content=file_content,
                taggun_data=taggun_data,
                company_vat=company_vat,
            )
        elif odoo_version == "V18":
            await odoo_process_v18(
                taggun_data=taggun_data,
                company_vat=company_vat,
            )
        else:
            raise NotImplementedError(
                f"La versión {odoo_version }: aún no ha sido implementada."
            )
    else:
        raise NotImplementedError(f"{invoice_processor} : No ha sido implementado aun.")

    logger.debug("Registro de cuenta contable completado")

    await save_file_dropbox(
        file=file,
        file_content=file_content,
        taggun_data=taggun_data,
        company_vat=company_vat,
    )
    logger.debug("Almacenamiento completado")
    logger.debug(f"[{file.filename}] Finalización exitosa para {company_vat}")


async def handle_multiple_invoice_scans(recipient: str, files: list[UploadFile]):
    # Leer todo el contenido de los archivos en paralelo
    contents = await asyncio.gather(*[file.read() for file in files])

    # Ejecutar procesamiento de cada archivo en paralelo
    results = await asyncio.gather(
        *[
            handle_invoice_scan(recipient=recipient, file=file, file_content=content)
            for file, content in zip(files, contents)
        ]
    )

    return results
