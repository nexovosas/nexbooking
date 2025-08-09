# app/booking/schemas/room_schema.py
from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing_extensions import Annotated

from .image_schema import ImageOut


# ---------- Image ----------
class ImageCreate(BaseModel):
    url: Annotated[
        HttpUrl,
        Field(description="URL of the room image", examples=["https://example.com/image.jpg"])
    ]


# ---------- Room Create ----------
class RoomCreate(BaseModel):
    room_type: Annotated[str, Field(min_length=2, max_length=100)]
    capacity: Annotated[int, Field(gt=0, le=50, description="Number of people the room can host")]
    amenities: Annotated[Optional[str], Field(None, max_length=500)]
    base_price: Annotated[float, Field(gt=0)]
    is_available: Annotated[Optional[bool], Field(default=True)]
    beds: Annotated[Optional[int], Field(default=1, ge=0, le=20)]
    accommodation_id: Annotated[int, Field(gt=0)]
    images: Annotated[
        Optional[List[ImageCreate]],
        Field(default=None, description="List of images for the room")
    ]


# ---------- Room Update ----------
class RoomUpdate(BaseModel):
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
    room_type: str
    capacity: int
    amenities: Optional[str] = None
    base_price: float
    is_available: bool
    beds: int
    accommodation_id: int
    images: List[ImageOut] = []

    model_config = ConfigDict(from_attributes=True)
