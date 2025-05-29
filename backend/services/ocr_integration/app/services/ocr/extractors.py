import difflib

from typing import Any, Dict, List
from app.core.settings import settings

import re
from typing import Dict, List


class RegexExtractor:
    def __init__(self):
        self.patterns = {
            "cif": r"[A-HJ-NP-SUVW]-?\d{7}[0-9A-J]\b(?![A-Za-z0-9])",
            "vat": r"[A-Za-z]{2}[A-Z0-9]{1}\d{7,8}\b(?![A-Za-z0-9])",
        }

    def extract_all_patterns(self, text: str) -> Dict[str, List[str]]:
        """Extracts all matches for all patterns."""
        results = set()
        for _, pattern in self.patterns.items():
            regex = re.compile(pattern)
            matches = regex.findall(text)
            valid_matches = [m.replace("-", "") for m in matches]
            results.update(valid_matches)

        return list(results)


class InvoiceExtractor:
    def __init__(self, json_data: Dict[str, Any]):
        self.ocr_data = json_data

    def extract_main_fields(self) -> Dict[str, Any]:
        """Extract main fields from OCR data."""
        partner_id = self.ocr_data.get("entities", {}).get("merchantName", {}).get(
            "data"
        ) or self.ocr_data.get("merchantName", {}).get("data", "")

        # Identificacion de en donde se hizo la compra
        tax_identification_supplier = self.ocr_data.get("entities", {}).get(
            "merchantVerification", {}
        ).get("data", {}).get("verificationId", "") or self.ocr_data.get(
            "merchantTaxId", {}
        ).get(
            "data", ""
        )

        invoice_date = self.ocr_data.get("date", {}).get("data", "")

        invoice_number = self.ocr_data.get("entities", {}).get("receiptNumber", {}).get(
            "data"
        ) or self.ocr_data.get("entities", {}).get("invoiceNumber", {}).get("data", "")

        amount_total = self.ocr_data.get("totalAmount", {}).get("data", 0.0)

        tax_amount = self.ocr_data.get("taxAmount", {}).get("data", 0.0)

        amount_untaxed = float(round(amount_total - tax_amount, 2))

        lines = self.extract_lines(amount_total)

        full_text = self.ocr_data.get("text", {}).get("text", "")

        regex_factory = RegexExtractor()

        valid_tax_identification = regex_factory.extract_all_patterns(text=full_text)

        if (
            tax_identification_supplier == settings.CIF
            or not tax_identification_supplier
        ):
            tax_identification_supplier = self.set_tax_identificacion_supplier(
                valid_tax_identification
            )

        address = {
            "address": self.ocr_data.get("merchantAddress", {}).get("data", ""),
            "city": self.ocr_data.get("merchantCity", {}).get("data", ""),
            "state": self.ocr_data.get("merchantState", {}).get("data", ""),
            "country_code": self.ocr_data.get("merchantCountryCode", {}).get(
                "data", ""
            ),
            "postal_code": self.ocr_data.get("merchantPostalCode", {}).get("data", ""),
        }

        return {
            "tax_identification_customer": settings.CIF,
            "tax_identification_supplier": tax_identification_supplier,
            "partner_id": partner_id,
            "invoice_date": invoice_date,
            "invoice_number": invoice_number,
            "amount_total": amount_total,
            "amount_untaxed": amount_untaxed,
            "tax_amount": tax_amount,
            "lines": lines,
            "address": address,
        }

    def extract_lines(self, amount_total: float) -> List[Dict[str, Any]]:
        items = self.ocr_data.get("entities", {}).get("productLineItems", [])
        lines = []

        for item in items:
            lines.append(
                {
                    "description": item["data"].get("name", {}).get("data", ""),
                    "quantity": item["data"].get("quantity", {}).get("data", 1),
                    "price_unit": item["data"].get("totalPrice", {}).get("data", 0.0),
                }
            )

        if not lines and "text" in self.ocr_data:
            lines.append(
                {
                    "description": "Servicio o Producto",
                    "quantity": 1,
                    "price_unit": amount_total,
                }
            )

        return lines

    def set_tax_identificacion_supplier(self, valid_tax_ids: List) -> str:

        threshold = 0.9

        filtered_tax_id = [
            tax_id
            for tax_id in valid_tax_ids
            if difflib.SequenceMatcher(None, settings.CIF, tax_id).ratio() < threshold
        ]

        if len(filtered_tax_id) == 1:
            return filtered_tax_id[0]
        else:
            return ""
