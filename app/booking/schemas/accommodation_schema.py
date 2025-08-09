# app/booking/schemas/accommodation_schema.py
from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing_extensions import Annotated

from .room_schema import RoomOut
from .image_schema import ImageOut


# ---------- Image ----------
class ImageCreate(BaseModel):
    url: Annotated[
        HttpUrl,
        Field(description="URL of the image", examples=["https://example.com/image.jpg"])
    ]
    alt_text: Annotated[
        Optional[str],
        Field(None, max_length=255, description="Alternative text for the image")
    ]


# ---------- Accommodation Create ----------
class AccommodationCreate(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=150)]
    location: Annotated[str, Field(min_length=2, max_length=150)]
    description: Annotated[Optional[str], Field(None, max_length=500)]
    services: Annotated[Optional[str], Field(None, max_length=300)]
    pet_friendly: Annotated[bool, Field(default=False)]
    type: Annotated[str, Field(min_length=2, max_length=50)]
    host_id: Annotated[int, Field(gt=0)]
    is_active: Annotated[bool, Field(default=True)]
    images: Annotated[
        Optional[List[ImageCreate]],
        Field(default=None, description="List of images for the accommodation")
    ]


# ---------- Accommodation Update ----------
class AccommodationUpdate(BaseModel):
    name: Annotated[Optional[str], Field(None, min_length=2, max_length=150)]
    location: Annotated[Optional[str], Field(None, min_length=2, max_length=150)]
    description: Annotated[Optional[str], Field(None, max_length=500)]
    services: Annotated[Optional[str], Field(None, max_length=300)]
    pet_friendly: Optional[bool] = None
    type: Annotated[Optional[str], Field(None, min_length=2, max_length=50)]
    host_id: Annotated[Optional[int], Field(None, gt=0)]
    is_active: Optional[bool] = None


# ---------- Accommodation Out ----------
class AccommodationOut(BaseModel):
    id: int
    name: str
    location: str
    description: Optional[str]
    services: Optional[str]
    pet_friendly: bool
    type: str
    host_id: int
    is_active: bool
    rooms: List[RoomOut] = []
    images: List[ImageOut] = []

    model_config = ConfigDict(from_attributes=True)
