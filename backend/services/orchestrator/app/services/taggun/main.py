import asyncio
from decimal import Decimal

from fastapi import UploadFile
from exponential_core.exceptions import CustomAppException

from app.core.logging import logger
from app.core.settings import settings
from app.core.secrets import SecretsService
from app.core.client_provider import ProviderConfig
from app.services.claudeai.client import ClaudeAIService
from app.services.claudeai.extract_line_items import (
    extract_claude_invoice_data,
    line_items_extraction,
)
from app.services.openai.client import OpenAIService
from app.services.zoho.processor import zoho_process
from app.services.upload.process import save_file_dropbox
from app.services.taggun.extractor import TaggunExtractor
from app.core.utils.tax_id_extractor import TaxIdExtractor
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.odoo.v16.processor import odoo_process as odoo_process_v16
from app.services.odoo.v18.processor import odoo_process as odoo_process_v18
from app.services.taggun.utils.formatter import (
    take_single_percent,
    validate_image_dimensions,
)

from .ocr import extract_ocr_payload
from .account_lookup import get_accounts_by_email
from .tax_id_matching import find_tax_ids, get_account_match
from .register import register_scan


async def handle_invoice_scan(
    recipient: str, file: UploadFile, file_content: bytes | None = None
):
    file_content = file_content or await file.read()
    logger.info(f"Inicia el Extraccion de {file.filename} para : {recipient}")

    validate_image_dimensions(file.filename, file_content)

    accounts_response = await get_accounts_by_email(email=recipient)
    all_tax_ids = [a.account_tax_id for a in accounts_response.accounts]

    config = ProviderConfig(server_url=settings.URL_OPENAPI)
    openai_service = OpenAIService(config=config)

    config = ProviderConfig(server_url=settings.URL_CLAUDEAPI)
    claudeai_service = ClaudeAIService(config)

    logger.info("Comienza extracción del servicio Taggun")
    payload = await extract_ocr_payload(file=file, file_content=file_content)
    logger.debug("Payload obtenido con éxito")

    taggun_extractor = TaggunExtractor(payload=payload)
    taggun_basic_fields = taggun_extractor.extrac_base_values()

    amount_discount = taggun_basic_fields.amount_discount
    amount_tax = taggun_basic_fields.amount_tax
    amount_total = taggun_basic_fields.amount_total
    amount_untaxed = taggun_basic_fields.amount_untaxed

    invoice_number = taggun_basic_fields.invoice_number

    tax_rate_percent: None | Decimal = None
    try:
        tax_candidate = taggun_extractor.calculate_tax_candidates(
            amount_discount=amount_discount,
            amount_tax=amount_tax,
            amount_total=amount_total,
            amount_untaxed=amount_untaxed,
        )

        if tax_candidate is not None:
            tax_rate_percent = take_single_percent(tax_candidate)

        corrected_values = taggun_extractor.corrected_values

        if corrected_values.get("amount_untaxed") is not None:
            amount_untaxed = corrected_values["amount_untaxed"]

        if corrected_values.get("amount_total") is not None:
            amount_total = corrected_values["amount_total"]

        if corrected_values.get("amount_tax") is not None:
            amount_tax = corrected_values["amount_tax"]

    except CustomAppException as ce:
        logger.error(f"Error en la validación de los valores obtenidos | {ce}")
        logger.debug("Intentando obtener valores con OpenAI")
        response = await openai_service.get_amounts(
            file=file, file_content=file_content
        )

        amount_tax = response.tax_amount.value
        amount_total = response.total.value
        amount_untaxed = response.subtotal.value
        amount_discount = response.discount_amount.value

        if response.tax_rate_percent is not None:
            tax_rate_percent = take_single_percent(response.tax_rate_percent)

        tax_rate_percent = (
            Decimal(str(response.tax_rate_percent)).copy_abs().quantize(Decimal("0.01"))
        )
        logger.debug("Valores obtenidos con éxito")

    address = taggun_extractor.extract_address()

    line_items = await taggun_extractor.parse_line_items(
        amount_untaxed=amount_untaxed,
    )

    if not line_items:
        logger.debug(f"La suma de los ítems no coincide con el total de la factura.")
        invoice_data = await extract_claude_invoice_data(
            file=file,
            file_content=file_content,
            claudeai_service=claudeai_service,
        )
        invoice_number = invoice_data.general_info.invoice_number
        line_items = await line_items_extraction(invoice_data=invoice_data)

    taggun_data = TaggunExtractedInvoice(
        partner_name=taggun_basic_fields.partner_name,
        partner_vat=taggun_basic_fields.partner_vat,
        date=taggun_basic_fields.date,
        invoice_number=invoice_number,
        amount_total=amount_total,
        amount_tax=amount_tax,
        amount_discount=amount_discount,
        amount_untaxed=amount_untaxed,
        address=address,
        line_items=line_items,
        tax_canditates=[tax_rate_percent],
    )

    payload_text = payload.get("text", {}).get("text", "")
    extractor = TaxIdExtractor(
        text=payload_text,
        all_tax_ids=all_tax_ids,
    )

    try:
        logger.info("Comienza búsqueda de los Tax ID")

        company_vat, partner_vat = find_tax_ids(extractor=extractor)
        taggun_data.partner_vat = partner_vat

    except CustomAppException as te:
        logger.error(f"Fallo en la búsqueda de los Tax ID : {te}")
        response = await openai_service.get_parties_tax_id(
            file=file,
            file_content=file_content,
        )
        logger.debug(response.model_dump(mode="json"))

        company_vat, partner_vat = extractor.resolve_company_and_partner_vat(
            supposed_company_vat=response.client_tax_it,
            supposed_partner_vat=response.partner_tax_it,
        )

        taggun_data.partner_vat = partner_vat
        taggun_data.partner_name = response.partner_name

    except Exception as e:
        raise CustomAppException(e)

    account = get_account_match(accounts_response, company_vat, extractor)
    company_vat = account.account_tax_id
    account_id = account.account_id

    await register_scan(
        user_id=accounts_response.user_id,
        account_id=account_id,
    )
    logger.info(
        f"Registro de escaneo completado para {account.account_name} - {company_vat} "
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
                openai_service=openai_service,
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
