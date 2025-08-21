# app/booking/schemas/availability_schema.py
from __future__ import annotations
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import Annotated

# ---------- Base ----------
class AvailabilityBase(BaseModel):
    date: Annotated[
        date,
        Field(
            description="Date for which the room availability is set",
            examples=["2025-08-15"]
        )
    ]
    price: Annotated[
        float,
        Field(
            ge=0,
            description="Price for the room on this date",
            examples=[350000.00]
        )
    ]
    room_id: Annotated[
        int,
        Field(
            gt=0,
            description="Associated room ID",
            examples=[101]
        )
    ]


# ---------- Create ----------
class AvailabilityCreate(AvailabilityBase):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "date": "2025-08-15",
                "price": 350000.00,
                "room_id": 101
            }
        ]
    })


# ---------- Update ----------
class AvailabilityUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "date": "2025-08-20",
                "price": 360000.00
            }
        ]
    })
    date: Annotated[Optional[date], Field(None, description="Updated date for availability", examples=["2025-08-20"])]
    price: Annotated[Optional[float], Field(None, ge=0, description="Updated price for this date", examples=[380000.00])]


# ---------- Output ----------
class AvailabilityOut(AvailabilityBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "date": "2025-08-15",
                    "price": 350000.00,
                    "status": "available",
                    "room_id": 101
                }
            ]
        }
    )
