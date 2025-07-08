from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta


class ZohoTokenResponse(BaseModel):
    ACCESS_TOKEN: str = Field(..., alias="access_token")
    REFRESH_TOKEN: Optional[str] = Field(None, alias="refresh_token")
    EXPIRES_AT: str

    @classmethod
    def from_response(cls, data: dict) -> "ZohoTokenResponse":
        now = datetime.now(timezone.utc)
        expires_in = data.get("expires_in", 3600)
        expires_at = (now + timedelta(seconds=expires_in)).isoformat()

        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            EXPIRES_AT=expires_at,
        )
