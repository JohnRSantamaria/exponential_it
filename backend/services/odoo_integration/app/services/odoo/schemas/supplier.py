from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, Union

from .enums import CompanyTypeEnum


class SupplierCreateSchema(BaseModel):
    name: str = Field(..., description="Nombre del proveedor")
    vat: str = Field(..., description="Identificación fiscal (NIT, CIF, etc.)")
    email: Optional[EmailStr] = Field(None, description="Correo del proveedor")
    phone: Optional[str] = Field(None, description="Teléfono del proveedor")
    company_type: CompanyTypeEnum = Field(
        default=CompanyTypeEnum.company,
        description="Tipo de entidad: 'company' o 'person'",
    )
    is_company: bool = Field(
        True,
        description="Indica si el partner es una empresa (True) o una persona natural (False)",
    )
    street: Optional[str] = Field(None, description="Calle y número del proveedor")
    zip: Optional[str] = Field(None, description="Código postal")
    city: Optional[str] = Field(None, description="Ciudad o municipio")
    state_id: Optional[int] = Field(None, description="ID del estado/provincia en Odoo")
    country_id: Optional[int] = Field(None, description="ID del país en Odoo")
    website: Optional[Union[str, HttpUrl]] = Field(
        None, description="Sitio web del proveedor"
    )

    def as_odoo_payload(self) -> dict:
        data = self.model_dump(exclude_none=True)
        data["supplier_rank"] = 1
        data["company_type"] = self.company_type.value
        if "website" in data:
            data["website"] = data["website"].strip()
        return data
