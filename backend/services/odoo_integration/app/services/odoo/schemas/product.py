from pydantic import BaseModel, Field
from typing import Optional

from app.services.odoo.schemas.enums import ProductTypeEnum


class ProductCreateSchema(BaseModel):
    name: str = Field(..., description="Nombre del producto")
    default_code: Optional[str] = Field(None, description="Referencia interna o SKU")
    barcode: Optional[str] = Field(None, description="Código de barras")
    list_price: float = Field(..., description="Precio de venta")
    detailed_type: ProductTypeEnum = Field(
        ProductTypeEnum.consu,
        description="Tipo de producto: 'consu' (consumible) o 'service' (servicio)",
    )
    uom_id: Optional[int] = Field(None, description="Unidad de medida")
    uom_po_id: Optional[int] = Field(None, description="Unidad de compra")
    taxes_id: Optional[list[int]] = Field(None, description="IDs de impuestos")

    def as_odoo_payload(self) -> dict:
        data = self.model_dump(exclude_none=True)
        if "tax_ids" in data:
            data["taxes_id"] = [(6, 0, data.pop("tax_ids"))]
        return data
