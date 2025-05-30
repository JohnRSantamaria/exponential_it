from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

from app.services.ocr.enums import InvoiceState


class InvoiceLine(BaseModel):
    product_id: Optional[int] = Field(None, title="ID del Producto")
    product_name: str = Field(..., title="Nombre del Producto")
    quantity: float = Field(..., title="Cantidad")
    price_unit: float = Field(..., title="Precio Unitario")
    discount: float = Field(..., title="Descuento")
    taxes: List = Field(default_factory=list, title="Impuestos")
    subtotal: float = Field(..., title="Subtotal")
    total: float = Field(..., title="Total")


class FacturaCompra(BaseModel):
    partner_id: int = Field(None, title="ID del Proveedor")
    partner_name: str = Field(None, title="Nombre del Proveedor")
    partner_vat: Optional[str] = Field(None, title="VAT del Proveedor")
    date_invoice: Optional[date] = Field(None, title="Fecha de la Factura")
    date_due: Optional[date] = Field(None, title="Fecha de Vencimiento")
    currency_id: Optional[str] = Field(None, title="Moneda")
    journal_id: Optional[int] = Field(None, title="ID del Diario Contable")
    invoice_origin: Optional[str] = Field(None, title="Origen de la Factura")
    state: Optional[InvoiceState] = Field(None, title="Estado de la Factura")
    invoice_line_ids: List[InvoiceLine] = Field(..., title="Líneas de Factura")
    amount_untaxed: Optional[float] = Field(None, title="Total sin Impuestos")
    amount_tax: Optional[float] = Field(None, title="Total de Impuestos")
    amount_total: Optional[float] = Field(None, title="Total de la Factura")
    payment_term_id: Optional[int] = Field(None, title="ID de Término de Pago")
    payment_reference: Optional[str] = Field(None, title="Referencia de Pago")
    company_id: Optional[int] = Field(None, title="ID de la Empresa")
    company_name: Optional[str] = Field(None, title="Nombre de la Empresa")


class ProveedorFactura(BaseModel):
    nombre: str = Field(None, title="Nombre del Proveedor")
    cif_nif: str = Field(None, title="CIF/NIF")
    direccion: Optional[str] = Field(None, title="Dirección")
    telefono: Optional[str] = Field(None, title="Teléfono")
    fax: Optional[str] = Field(None, title="Fax")
    email: Optional[str] = Field(None, title="Email")
    web: Optional[str] = Field(None, title="Sitio Web")
