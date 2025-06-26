from pydantic import BaseModel, Field, field_validator


class TaxesResponse(BaseModel):
    tax_id: str
    tax_percentage: float
    tax_account_id: str
    is_active: bool = Field(..., alias="status")

    @field_validator("is_active", mode="before")
    @classmethod
    def status_to_bool(cls, v):
        return v.lower() == "active" if isinstance(v, str) else False
