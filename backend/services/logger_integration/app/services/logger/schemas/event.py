# app/services/logger/schemas/event.py
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, NonNegativeInt, ConfigDict
from typing import Literal, Optional, Any
from decimal import Decimal
import uuid, datetime, re

Status = Literal["completed", "failed"]

# Si quieres controlar pasos, puedes usar Literal[...] aquí
# Step = Literal["authorize_read", "ocr", "extract_totals", "post_to_odoo", "done"]


class EventSchema(BaseModel):
    # --- core ---
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    ts: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    # --- negocio ---
    invoice_id: str = Field(..., max_length=128)
    step: str = Field(..., max_length=64)  # o: Step si quieres fijar valores
    status: Status
    service: str = Field(..., max_length=64)
    request_id: str = Field(..., max_length=128)

    # --- opcionales/contexto ---
    user: Optional[str] = Field(default=None, max_length=128)
    date: Optional[datetime.date] = None
    file_name: Optional[str] = Field(default=None, max_length=256)

    partner_cif: Optional[str] = Field(
        default=None, max_length=64, pattern=r"^[A-Z0-9\-\.]+$"
    )  # simple
    partner_name: Optional[str] = Field(default=None, max_length=256)

    amount_total: Optional[Decimal] = Field(
        default=None
    )  # 2 decimales lógico a nivel DB
    amount_tax: Optional[Decimal] = Field(default=None)

    time_process: Optional[NonNegativeInt] = None  # milisegundos >= 0
    error: Optional[str] = None
    recommendations: Optional[str] = None

    meta: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        # Si prefieres serializar Decimal como string para evitar binarios:
        ser_json_timedelta="iso8601",  # por si luego agregas timedelta
        json_encoders={Decimal: lambda v: str(v)},  # o float(v) si quieres número
        extra="ignore",
    )

    @field_validator("ts")
    @classmethod
    def ensure_tz_aware(cls, v: datetime.datetime) -> datetime.datetime:
        return v if v.tzinfo else v.replace(tzinfo=datetime.timezone.utc)
