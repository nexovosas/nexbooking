# app/booking/schemas/booking_schema.py
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing_extensions import Annotated


# ---------- Earnings Report ----------
class EarningsReport(BaseModel):
    total_earnings: Annotated[float, Field(ge=0, description="Total earnings for the given period")]


# ---------- Booking Status Enum ----------
class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


# ---------- Base Schema ----------
class BookingBase(BaseModel):
    user_id: Annotated[int, Field(gt=0, description="User ID making the booking")]
    room_id: Annotated[int, Field(gt=0, description="Booked room ID")]
    start_date: Annotated[date, Field(description="Check-in date")]
    end_date: Annotated[date, Field(description="Check-out date")]
    guests: Annotated[int, Field(ge=1, le=50, description="Number of guests (1 to 50)")]


# ---------- Booking Create ----------
class BookingCreate(BookingBase):
    @model_validator(mode="after")
    def validate_dates(self) -> "BookingCreate":
        """Ensure the end date is after the start date."""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self


# ---------- Booking Update ----------
class BookingUpdate(BaseModel):
    start_date: Annotated[Optional[date], Field(None, description="New check-in date")]
    end_date: Annotated[Optional[date], Field(None, description="New check-out date")]
    guests: Annotated[Optional[int], Field(None, ge=1, le=50)]
    status: Optional[BookingStatus] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "BookingUpdate":
        """If both dates are provided, ensure the end date is after the start date."""
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self


# ---------- Booking Output ----------
class BookingOut(BookingBase):
    id: int
    status: BookingStatus
    code: Annotated[str, Field(min_length=4, max_length=50, description="Unique booking code")]
    total_price: Annotated[float, Field(ge=0, description="Total amount for the booking")]

    model_config = ConfigDict(from_attributes=True)
