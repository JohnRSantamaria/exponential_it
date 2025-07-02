import asyncio
from fastapi import UploadFile
from app.services.odoo.processor import odoo_process
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
    logger.debug(f"[{file.filename}] Inicia el proceso")
    file_content = file_content or await file.read()

    logger.debug(f"Inicia el Extraccion de datos para : {recipient}")
    accounts_response = await get_accounts_by_email(email=recipient)
    all_tax_ids = [a.account_tax_id for a in accounts_response.accounts]

    payload = await extract_ocr_payload(file=file, file_content=file_content)
    taggun_data = extract_taggun_data(payload)

    payload_text = payload.get("text", {}).get("text", "")
    company_vat, partner_vat, extractor = find_tax_ids(payload_text, all_tax_ids)
    taggun_data.partner_vat = partner_vat

    account = get_account_match(accounts_response, company_vat, extractor)

    await register_scan(
        user_id=accounts_response.user_id,
        account_id=account.account_id,
    )
    logger.debug("Registro de escaneo completado")

    secrets_service = await SecretsService(company_vat=company_vat).load()
    if secrets_service.get_invoice_processor() == "ZOHO":
        await zoho_process(
            file=file,
            file_content=file_content,
            taggun_data=taggun_data,
        )
    else:
        await odoo_process(
            taggun_data,
            company_vat,
        )

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
