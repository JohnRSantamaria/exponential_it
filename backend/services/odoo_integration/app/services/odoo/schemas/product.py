from typing import List, Optional
from pydantic import Field, field_validator

from exponential_core.odoo.enums import ProductTypeEnum
from exponential_core.odoo.schemas.base import BaseSchema
from exponential_core.odoo.schemas.normalizers import normalize_empty_string


class ProductCreateSchema(BaseSchema):
    name: str = Field(..., description="Nombre del producto")
    default_code: Optional[str] = Field(None, description="Referencia interna o SKU")
    barcode: Optional[str] = Field(None, description="Código de barras")
    list_price: float = Field(..., description="Precio de venta")
    detailed_type: ProductTypeEnum = Field(
        ProductTypeEnum.CONSU,
        description="Tipo de producto: 'consu' (consumible) o 'service' (servicio)",
    )
    uom_id: Optional[int] = Field(None, description="Unidad de medida")
    uom_po_id: Optional[int] = Field(None, description="Unidad de compra")
    taxes_id: Optional[List[int]] = Field(None, description="IDs de impuestos")

    # 💡 Normalización de campos str opcionales
    @field_validator("default_code", "barcode", mode="before")
    @classmethod
    def normalize_empty_fields(cls, v):
        return normalize_empty_string(v)

    def transform_payload(self, data: dict) -> dict:
        if "tax_ids" in data:
            data["taxes_id"] = [(6, 0, data.pop("tax_ids"))]
        return data


class ProductCreateSchemaV18(BaseSchema):
    """
    Esquema para crear productos compatible con Odoo v18 y anteriores.
    Usa 'type' en vez de 'detailed_type' y no incluye campos modernos como 'uom_po_id'.
    """

    name: str = Field(..., description="Nombre del producto")
    default_code: Optional[str] = Field(None, description="Referencia interna o SKU")
    barcode: Optional[str] = Field(None, description="Código de barras")
    list_price: float = Field(..., description="Precio de venta")
    type: ProductTypeEnum = Field(
        ProductTypeEnum.CONSU,
        description="Tipo de producto: 'product' (almacenable), 'consu' (consumible) o 'service' (servicio)",
    )
    uom_id: Optional[int] = Field(None, description="Unidad de medida")
    taxes_id: Optional[List[int]] = Field(None, description="IDs de impuestos")

    @field_validator("default_code", "barcode", mode="before")
    @classmethod
    def normalize_empty_fields(cls, v):
        return normalize_empty_string(v)

    def transform_payload(self, data: dict) -> dict:
        if "tax_ids" in data:
            data["taxes_id"] = [(6, 0, data.pop("tax_ids"))]
        return data
