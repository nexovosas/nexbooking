# app/booking/schemas/availability_schema.py
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import Annotated


# ---------- Base ----------
class AvailabilityBase(BaseModel):
    date: Annotated[date, Field(description="Date for which the room availability is set")]
    price: Annotated[float, Field(ge=0, description="Price for the room on this date")]
    room_id: Annotated[int, Field(gt=0, description="Associated room ID")]


# ---------- Create ----------
class AvailabilityCreate(AvailabilityBase):
    pass


# ---------- Update ----------
class AvailabilityUpdate(BaseModel):
    date: Annotated[Optional[date], Field(None, description="Updated date for availability")]
    price: Annotated[Optional[float], Field(None, ge=0, description="Updated price for this date")]


# ---------- Output ----------
class AvailabilityOut(AvailabilityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
