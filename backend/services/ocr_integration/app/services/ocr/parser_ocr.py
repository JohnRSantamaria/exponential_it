from app.services.admin.schemas import CredentialOut
from app.services.ocr.extractor import InvoiceExtractor
from app.services.ocr.schemas import Invoice, Supplier


def parser_invoice(cif: CredentialOut, ocr_data: dict) -> Invoice:
    """
    Procesa datos OCR y devuelve una factura estructurada.
    Retorna None si ocurre un error.
    """
    parser = InvoiceExtractor(ocr_data, cif)
    invoice = parser.extract_invoice()
    lines = parser.extract_lines(invoice.amount_total)
    invoice.invoice_lines = lines

    return invoice


def parser_supplier(cif: CredentialOut, ocr_data: dict) -> Supplier:
    """"""
    parser = InvoiceExtractor(ocr_data, cif)
    return parser.extract_supplier()
