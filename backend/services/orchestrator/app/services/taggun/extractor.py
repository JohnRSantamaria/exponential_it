from datetime import datetime

from app.core.settings import settings
from app.services.zoho.exceptions import TaxPercentageNotFound
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

    @staticmethod
    def normalize(value: float, tolerance: float = 0.03) -> float:
        rounded = round(value, 2)
        for standard in settings.TAX_STANDARD_RATES:
            if abs(rounded - standard) <= tolerance:
                return standard
        return rounded

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
        amount_total = self.safe_float(self.try_paths(["totalAmount", "data"]))
        amount_untaxed = self.safe_float(self.try_paths(["paidAmount", "data"]))

        parsed_items: list[LineItemSchema] = []

        total_units = 0
        total_price_sum = 0.0
        total_unit_price_sum = 0.0

        for item in raw_items:
            data = item.get("data", {})

            product_name = data.get("name", {}).get("data", "").strip()
            quantity = data.get("quantity", {}).get("data", 0)
            unit_price = self.safe_float(data.get("unitPrice", {}).get("data"))
            total_price = self.safe_float(data.get("totalPrice", {}).get("data"))

            # Acumuladores
            total_units += quantity
            total_price_sum += total_price
            total_unit_price_sum += unit_price

            # Crear instancia del esquema y agregarla a la lista
            parsed_items.append(
                LineItemSchema(
                    name=product_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                )
            )

        if total_unit_price_sum > amount_untaxed or total_price_sum > amount_total:
            return [
                LineItemSchema(
                    name="Ajuste de Totales",
                    quantity=1,
                    unit_price=amount_untaxed,
                    total_price=amount_total,
                )
            ]
        return parsed_items

    def reorder(self):
        amount_total = self.safe_float(self.try_paths(["totalAmount", "data"]))
        amount_tax = self.safe_float(self.try_paths(["taxAmount", "data"]))
        amount_untaxed = self.safe_float(self.try_paths(["paidAmount", "data"]))
        amount_discount = self.safe_float(self.try_paths(["discountAmount", "data"]))

        # Casos inválidos: todo cero o iguales
        if amount_total <= 0 and amount_untaxed <= 0 and amount_tax <= 0:
            raise TaxPercentageNotFound(data={...})
        if amount_total == amount_untaxed == amount_tax:
            raise TaxPercentageNotFound(data={...})

        # Si falta untaxed, lo calculamos
        if amount_untaxed <= 0 and amount_total > 0 and amount_tax > 0:
            amount_untaxed = amount_total - amount_tax

        # Si hay descuento, ajustamos untaxed
        if amount_discount > 0:
            amount_untaxed = amount_total + amount_discount - amount_tax

        # Si falta tax, lo calculamos
        if amount_tax <= 0 and amount_total > 0 and amount_untaxed > 0:
            amount_tax = amount_total - amount_untaxed

        values = [amount_total, amount_untaxed, amount_tax]
        values.sort(reverse=True)
        self.ocr_data["totalAmount"]["data"] = values[0]
        self.ocr_data["paidAmount"]["data"] = values[1]
        self.ocr_data["taxAmount"]["data"] = values[2]

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
        self.reorder()

        amount_total = self.try_paths(["totalAmount", "data"])
        amount_tax = self.try_paths(["taxAmount", "data"])
        amount_untaxed = self.try_paths(["paidAmount", "data"])
        amount_discount = self.try_paths(["discountAmount", "data"])

        address = self.extract_address()
        lines = self.parse_line_items()

        return TaggunExtractedInvoice(
            partner_name=partner_name,
            partner_vat=partner_vat,
            date=date_invoice,
            invoice_number=invoice_number,
            amount_total=amount_total,
            amount_tax=amount_tax,
            amount_untaxed=amount_untaxed,
            amount_discount=amount_discount or 0,
            address=address,
            line_items=lines,
        )
