from pydantic import BaseModel


class BillsResponse(BaseModel):
    bill_id: str
    bill_number: str
    vendor_id: str
