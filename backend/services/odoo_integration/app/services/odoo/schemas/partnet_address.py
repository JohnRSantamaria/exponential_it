from pydantic import BaseModel, Field
from typing import Optional

from .enums import AddressTypeEnum


class AddressCreateSchema(BaseModel):
    partner_id: int = Field(
        ..., description="ID del partner principal (cliente o proveedor)"
    )
    address_name: str = Field(
        ..., description="Nombre de la dirección (ej. 'Bodega norte')"
    )
    street: str = Field(..., description="Calle y número")
    city: str = Field(..., description="Ciudad o municipio")
    address_type: AddressTypeEnum = Field(
        default=AddressTypeEnum.invoice,
        description=(
            "Tipo de dirección:\n"
            "- contact: Contacto (detalles de empleados)\n"
            "- invoice: Dirección de factura\n"
            "- delivery: Dirección de entrega\n"
            "- private: Dirección privada\n"
            "- other: Otra dirección (subsidiarias u otras)"
        ),
    )
    zip: Optional[str] = Field(None, description="Código postal")
    state_id: Optional[int] = Field(None, description="ID del estado o provincia")
    country_id: Optional[int] = Field(None, description="ID del país")
    phone: Optional[str] = Field(None, description="Teléfono fijo (si aplica)")

    def as_odoo_payload(self) -> dict:
        payload = self.model_dump(exclude_none=True)

        # Renombrar campos
        payload["name"] = payload.pop("address_name")
        payload["parent_id"] = payload.pop("partner_id")
        payload["type"] = payload.pop("address_type").value

        return payload
