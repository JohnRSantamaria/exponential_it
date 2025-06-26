from pydantic import BaseModel, Field, field_validator


class ContactResponse(BaseModel):
    contact_id: str
    contact_name: str
    is_active: bool = Field(..., alias="status")
    cf_cif: str

    @field_validator("is_active", mode="before")
    @classmethod
    def status_to_bool(cls, v):
        return v.lower() == "active" if isinstance(v, str) else False

    @field_validator("cf_cif")
    @classmethod
    def validate_cf_cif(cls, v):
        if not v or not isinstance(v, str) or v.strip() == "":
            raise ValueError("El campo 'cf_cif' es obligatorio y no puede estar vacío.")
        return v
