from typing import List
from pydantic import BaseModel, Field

from app.services.taggun.schemas.taggun_models import LineItemSchema
from exponential_core.odoo import ResponseTaxesSchema


class ClasificacionRequest(BaseModel):
    provider: str = Field(..., description="Nombre del proveedor")
    nif: str = Field(..., description="NIF del proveedor")
    products: List[LineItemSchema] = Field(
        ..., description="Líneas de producto detectadas en la factura"
    )
    iva_rate: float = Field(
        ..., description="Porcentaje de IVA detectado en la factura"
    )
    candidate_tax_ids: List[ResponseTaxesSchema] = Field(
        ..., description="Impuestos disponibles en Odoo con ese porcentaje"
    )


class TaxIdResponseSchema(BaseModel):
    tax_id_number: int
    description: str
