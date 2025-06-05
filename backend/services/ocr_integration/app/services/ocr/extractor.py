from datetime import datetime
from typing import Any, Dict, List

from app.services.ocr.enums import InvoiceState
from app.services.admin.schemas import CredentialOut
from app.services.ocr.schemas import Invoice, InvoiceLine, Supplier


class InvoiceExtractor:
    def __init__(self, ocr_data: Dict[str, Any], cif: CredentialOut):
        self.ocr_data = ocr_data
        self.cif = cif

    def extract_invoice(self) -> Invoice:

        partner_name = self.ocr_data.get("entities", {}).get("merchantName", {}).get(
            "data"
        ) or self.ocr_data.get("merchantName", {}).get("data", "")

        partner_vat = self.ocr_data.get("entities", {}).get(
            "merchantVerification", {}
        ).get("data", {}).get("verificationId", "") or self.ocr_data.get(
            "merchantTaxId", {}
        ).get(
            "data", ""
        )

        raw_date = self.ocr_data.get("date", {}).get("data")
        try:
            date_invoice = (
                datetime.fromisoformat(raw_date.replace("Z", "+00:00")).date()
                if raw_date
                else None
            )
        except Exception:
            date_invoice = None

        invoice_origin = self.ocr_data.get("entities", {}).get("receiptNumber", {}).get(
            "data"
        ) or self.ocr_data.get("entities", {}).get("invoiceNumber", {}).geft("data", "")

        amount_total = float(self.ocr_data.get("totalAmount", {}).get("data", 0.0))
        amount_tax = float(self.ocr_data.get("taxAmount", {}).get("data", 0.0))
        amount_untaxed = round(amount_total - amount_tax, 2)

        invoice = Invoice(
            partner_id=None,
            partner_name=partner_name,
            partner_vat=partner_vat,
            date_invoice=date_invoice,
            invoice_origin=invoice_origin,
            state=InvoiceState.draft,  # TODO : Hay que preguntar como se optiene o se deja Draft
            invoice_lines=[],
            amount_total=amount_total,
            amount_tax=amount_tax,
            amount_untaxed=amount_untaxed,
            company_id=self.cif,
        )

        return invoice

    def extract_supplier(self) -> Supplier:
        return Supplier(
            name=self.ocr_data.get("merchantName", {}).get("data", ""),
            vat=self.ocr_data.get("merchantTaxId", {}).get("data", ""),
            address={
                "street": self.ocr_data.get("merchantAddress", {}).get("data", ""),
                "city": self.ocr_data.get("merchantCity", {}).get("data", ""),
                "state": self.ocr_data.get("merchantState", {}).get("data", ""),
                "country_code": self.ocr_data.get("merchantCountryCode", {}).get(
                    "data", ""
                ),
                "postal_code": self.ocr_data.get("merchantPostalCode", {}).get(
                    "data", ""
                ),
            },
            phone=self.ocr_data.get("merchantPhoneNumber", {}).get("data", ""),
            fax=self.ocr_data.get("merchantFax", {}).get("data", ""),
            email=self.ocr_data.get("merchantEmail", {}).get("data", ""),
            website=self.ocr_data.get("merchantWebsite", {}).get("data", ""),
        )

    def extract_lines(self, amount_total: float) -> List[InvoiceLine]:
        items = self.ocr_data.get("entities", {}).get("productLineItems", [])
        lines = []

        for item in items:
            data = item.get("data", {})
            product_name = data.get("name", {}).get("data", "")
            quantity = float(data.get("quantity", {}).get("data", 1))
            price_unit = float(data.get("unitPrice", {}).get("data", 0.0))
            total_price = float(data.get("total¨Price", {}).get("data", 0.0))
            subtotal = round(quantity * price_unit, 2)

            line = InvoiceLine(
                product_id=None,
                product_name=product_name,
                quantity=quantity,
                price_unit=price_unit,
                discount=0.0,
                subtotal=subtotal,
                total=total_price,
            )
            lines.append(line)

        # Caso de fallback si no hay líneas reconocidas
        if not lines and "text" in self.ocr_data:
            fallback_line = InvoiceLine(
                product_id=None,
                product_name="Servicio o Producto",
                quantity=1,
                price_unit=amount_total,
                discount=0.0,
                taxes=[],
                subtotal=amount_total,
                total=amount_total,
            )
            lines.append(fallback_line)

        return lines
