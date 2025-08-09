# app/booking/schemas/image_schema.py
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing_extensions import Annotated


# ---------- Create ----------
class ImageCreate(BaseModel):
    url: Annotated[HttpUrl, Field(description="Full URL of the image")]
    alt_text: Annotated[Optional[str], Field(None, max_length=255, description="Alternative text for accessibility")]


# ---------- Output ----------
class ImageOut(BaseModel):
    id: int
    url: Annotated[HttpUrl, Field(description="Full URL of the image")]
    room_id: Annotated[Optional[int], Field(None, description="ID of the associated room")]
    accommodation_id: Annotated[Optional[int], Field(None, description="ID of the associated accommodation")]

    model_config = ConfigDict(from_attributes=True)
