# app/booking/schemas/room_schema.py
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing_extensions import Annotated

from .image_schema import ImageOut

# ---------- Image ----------
class ImageCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "url": "https://cdn.nexovo.com/images/la-montera-suite.jpg"
            }
        ]
    })
    url: Annotated[
        HttpUrl,
        Field(
            description="URL of the room image",
            examples=["https://cdn.nexovo.com/images/la-montera-suite.jpg"]
        )
    ]


# ---------- Room Create ----------
class RoomCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "room_name": "H-001",
                "room_type": "Suite Deluxe",
                "capacity": 2,
                "amenities": "WiFi,Jacuzzi,Breakfast included",
                "base_price": 450000.00,
                "is_available": True,
                "beds": 1,
                "accommodation_id": 1,
                "images": [
                    {
                        "url": "https://cdn.nexovo.com/images/la-montera-suite.jpg"
                    }
                ]
            }
        ]
    })
    room_name: Annotated[str, Field(min_length=5, max_length=50, examples=["H-001"])]
    room_type: Annotated[str, Field(min_length=2, max_length=100, examples=["Suite Deluxe"])]
    capacity: Annotated[int, Field(gt=0, le=50, description="Number of people the room can host", examples=[2])]
    amenities: Annotated[Optional[str], Field(None, max_length=500, examples=["WiFi,Jacuzzi,Breakfast included"])]
    base_price: Annotated[float, Field(gt=0, examples=[450000.00])]
    is_available: Annotated[Optional[bool], Field(default=True, examples=[True])]
    beds: Annotated[Optional[int], Field(default=1, ge=0, le=20, examples=[1])]
    accommodation_id: Annotated[int, Field(gt=0, examples=[1])]
    images: Annotated[
        Optional[List[ImageCreate]],
        Field(default=None, description="List of images for the room")
    ]


# ---------- Room Update ----------
class RoomUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "base_price": 480000.00,
                "is_available": False
            },
            {
                "room_type": "Suite Deluxe Renovada",
                "amenities": "WiFi,Jacuzzi,Breakfast included,Air conditioning"
            }
        ]
    })
    room_type: Annotated[Optional[str], Field(None, min_length=2, max_length=100)]
    capacity: Annotated[Optional[int], Field(None, gt=0, le=50)]
    amenities: Annotated[Optional[str], Field(None, max_length=500)]
    base_price: Annotated[Optional[float], Field(None, gt=0)]
    is_available: Optional[bool] = None
    beds: Annotated[Optional[int], Field(None, ge=0, le=20)]
    accommodation_id: Annotated[Optional[int], Field(None, gt=0)]


# ---------- Room Out ----------
class RoomOut(BaseModel):
    id: int
    room_name: str
    room_type: str
    capacity: int
    amenities: Optional[str] = None
    base_price: float
    is_available: bool
    beds: int
    accommodation_id: int
    images: List[ImageOut] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 10,
                    "room_name": "H-001",
                    "room_type": "Suite Deluxe",
                    "capacity": 2,
                    "amenities": "WiFi,Jacuzzi,Breakfast included",
                    "base_price": 450000.00,
                    "is_available": True,
                    "beds": 1,
                    "accommodation_id": 1,
                    "images": [
                        {
                            "id": 101,
                            "url": "https://cdn.nexovo.com/images/la-montera-suite.jpg",
                            "room_id": 10,
                            "accommodation_id": 1
                        }
                    ]
                }
            ]
        }
    )
