from app.core.interface.account_provider import AccountingProvider
from app.services.ocr.schemas import Invoice


async def find_matching_account_id(invoice: Invoice, provider: AccountingProvider):
    pass
