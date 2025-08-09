# app/booking/schemas/booking_schema.py
from __future__ import annotations
from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing_extensions import Annotated

# ---------- Earnings Report ----------
class EarningsReport(BaseModel):
    total_earnings: Annotated[
        float,
        Field(
            ge=0,
            description="Total earnings for the given period",
            examples=[1250000.00]
        )
    ]


# ---------- Booking Status Enum ----------
class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


# ---------- Base Schema ----------
class BookingBase(BaseModel):
    user_id: Annotated[int, Field(gt=0, description="User ID making the booking", examples=[5])]
    room_id: Annotated[int, Field(gt=0, description="Booked room ID", examples=[101])]
    start_date: Annotated[date, Field(description="Check-in date", examples=["2025-08-15"])]
    end_date: Annotated[date, Field(description="Check-out date", examples=["2025-08-20"])]
    guests: Annotated[int, Field(ge=1, le=50, description="Number of guests (1 to 50)", examples=[2])]


# ---------- Booking Create ----------
class BookingCreate(BookingBase):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "user_id": 5,
                "room_id": 101,
                "start_date": "2025-08-15",
                "end_date": "2025-08-20",
                "guests": 2
            }
        ]
    })

    @model_validator(mode="after")
    def validate_dates(self) -> "BookingCreate":
        """Ensure the end date is after the start date."""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self


# ---------- Booking Update ----------
class BookingUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "start_date": "2025-08-16",
                "end_date": "2025-08-22",
                "guests": 3,
                "status": "confirmed"
            },
            {
                "status": "cancelled"
            }
        ]
    })
    start_date: Annotated[Optional[date], Field(None, description="New check-in date", examples=["2025-08-16"])]
    end_date: Annotated[Optional[date], Field(None, description="New check-out date", examples=["2025-08-22"])]
    guests: Annotated[Optional[int], Field(None, ge=1, le=50, examples=[3])]
    status: Optional[BookingStatus] = Field(default=None, examples=["confirmed"])

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
    code: Annotated[str, Field(min_length=4, max_length=50, description="Unique booking code", examples=["BK-2025-0001"])]
    total_price: Annotated[float, Field(ge=0, description="Total amount for the booking", examples=[1750000.00])]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "user_id": 5,
                    "room_id": 101,
                    "start_date": "2025-08-15",
                    "end_date": "2025-08-20",
                    "guests": 2,
                    "status": "confirmed",
                    "code": "BK-2025-0001",
                    "total_price": 1750000.00
                }
            ]
        }
    )
