from datetime import datetime

from app.core.logging import logger
from app.core.utils.tax_resolver import TaxCalculator
from app.services.taggun.exceptions import FieldNotFoundError
from app.services.taggun.schemas.taggun_models import (
    AddressSchema,
    LineItemSchema,
    TaggunExtractedInvoice,
)


class TaggunExtractor:
    def __init__(self, payload):
        self.ocr_data = payload

    def try_paths(self, *paths, default=""):
        for path in paths:
            value = self.ocr_data
            for key in path:
                try:
                    value = value[key]
                except (KeyError, TypeError):
                    value = None
                    break
            if value is not None:
                return value
        return default

    @staticmethod
    def safe_float(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_iso_date(value: str):
        """
        Intenta convertir una cadena ISO (como '2024-01-01T00:00:00Z') en un objeto `date`.
        Retorna None si no es válida.
        """
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except Exception:
            return None

    def extract_address(self) -> AddressSchema:
        return AddressSchema(
            street=self.try_paths(["merchantAddress", "data"]),
            city=self.try_paths(["merchantCity", "data"]),
            state=self.try_paths(["merchantState", "data"]),
            country_code=self.try_paths(["merchantCountryCode", "data"]),
            postal_code=self.try_paths(["merchantPostalCode", "data"]),
            phone=self.try_paths(["merchantPhoneNumber", "data"]),
            fax=self.try_paths(["merchantFax", "data"]),
            email=self.try_paths(["merchantEmail", "data"]),
            website=self.try_paths(["merchantWebsite", "data"]),
        )

    def extract_line_items(self) -> list:
        items = self.try_paths(["entities", "productLineItems"], default=[])
        return items if isinstance(items, list) else []

    def parse_line_items(self) -> list[LineItemSchema]:
        raw_items = self.extract_line_items()
        parsed_items: list[LineItemSchema] = []

        amount_total = self.safe_float(self.try_paths(["totalAmount", "data"]))
        amount_tax = self.safe_float(self.try_paths(["taxAmount", "data"]))
        amount_untaxed = self.safe_float(self.try_paths(["paidAmount", "data"]))
        amount_discount = self.safe_float(self.try_paths(["discountAmount", "data"]))

        calculator = TaxCalculator(
            amount_discount=amount_discount,
            amount_tax=amount_tax,
            amount_total=amount_total,
            amount_untaxed=amount_untaxed,
        )

        calculator.reorder(
            amount_tax=amount_tax,
            amount_untaxed=amount_untaxed,
            amount_total=amount_total,
            amount_discount=amount_discount,
        )

        for item in raw_items:
            data = item.get("data", {})

            product_name = data.get("name", {}).get("data", "")
            quantity = data.get("quantity", {}).get("data", 0)
            unit_price = self.safe_float(data.get("unitPrice", {}).get("data"))
            total_price = self.safe_float(data.get("totalPrice", {}).get("data"))

            # ? En caso de que sea mayor que el valor total que el unitprice dado que este va sin taxes lo remplazamos
            if unit_price >= calculator.amount_total:
                unit_price = calculator.amount_untaxed

            if total_price < unit_price:
                total_price = calculator.amount_total

            parsed_items.append(
                LineItemSchema(
                    name=product_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                )
            )

        return parsed_items

    def extract_data(self) -> TaggunExtractedInvoice:
        partner_name = self.try_paths(
            ["merchantName", "data"],
            ["entities", "merchantName", "data"],
        )

        partner_vat = self.try_paths(
            ["merchantTaxId", "data"],
            ["entities", "merchantVerification", "data", "verificationId"],
        )

        raw_date = self.try_paths(["date", "data"])
        date_invoice = self.parse_iso_date(raw_date)

        invoice_number = self.try_paths(
            ["invoiceNumber", "data"],
            ["entities", "invoiceNumber", "data"],
        )

        amount_total = self.safe_float(self.try_paths(["totalAmount", "data"]))
        amount_tax = self.safe_float(self.try_paths(["taxAmount", "data"]))
        amount_untaxed = self.safe_float(self.try_paths(["paidAmount", "data"]))
        amount_discount = self.safe_float(self.try_paths(["discountAmount", "data"]))

        calculator = TaxCalculator(
            amount_discount=amount_discount,
            amount_total=amount_total,
            amount_untaxed=amount_untaxed,
            amount_tax=amount_tax,
        )
        calculator.reorder(
            amount_total=amount_total,
            amount_untaxed=amount_untaxed,
            amount_tax=amount_tax,
            amount_discount=amount_discount,
        )

        address = self.extract_address()
        lines = self.parse_line_items()

        return TaggunExtractedInvoice(
            partner_name=partner_name,
            partner_vat=partner_vat,
            date=date_invoice,
            invoice_number=invoice_number,
            amount_total=calculator.amount_total,
            amount_tax=calculator.amount_tax,
            amount_untaxed=calculator.amount_untaxed,
            amount_discount=calculator.amount_discount,
            address=address,
            line_items=lines,
        )
