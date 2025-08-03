from openai import BaseModel


class PartnerRequest(BaseModel):
    partner_name: str
