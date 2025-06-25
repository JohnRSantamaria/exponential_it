from fastapi import UploadFile
from app.services.upload.process import save_file_dropbox
from app.services.zoho.main import zoho_process
from .ocr import extract_ocr_payload, extract_taggun_data
from .account_lookup import get_accounts_by_email
from .tax_id_matching import find_tax_ids, get_account_match
from .register import register_scan


async def handle_invoice_scan(recipient: str, file: UploadFile):

    file_content = await file.read()

    payload = await extract_ocr_payload(file=file, file_content=file_content)
    taggun_data = extract_taggun_data(payload)

    accounts_response = await get_accounts_by_email(email=recipient)
    all_tax_ids = [a.account_tax_id for a in accounts_response.accounts]

    payload_text = payload.get("text", {}).get("text", "")
    company_vat, partner_vat, extractor = find_tax_ids(payload_text, all_tax_ids)
    taggun_data.partner_vat = partner_vat

    account = get_account_match(accounts_response, company_vat, extractor)

    await register_scan(
        user_id=accounts_response.user_id,
        account_id=account.account_id,
    )

    await zoho_process(
        file=file,
        file_content=file_content,
        taggun_data=taggun_data,
    )

    await save_file_dropbox(
        file=file,
        file_content=file_content,
        taggun_data=taggun_data,
        company_vat=company_vat,
    )
