# app/booking/schemas/image_schema.py
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing_extensions import Annotated

# ---------- Create ----------
class ImageCreate(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
        "examples": [
            {
                "url": "https://cdn.nexovo.com/images/la-montera-front.jpg",
                "alt_text": "Front view of La Montera Hotel"
            },
            {
                "url": "https://cdn.nexovo.com/images/la-montera-room.jpg",
                "alt_text": "Luxury room with mountain view"
            }
        ]
    })
    url: Annotated[
        HttpUrl,
        Field(
            description="Full URL of the image",
            examples=["https://cdn.nexovo.com/images/la-montera-front.jpg"]
        )
    ]
    alt_text: Annotated[
        Optional[str],
        Field(
            default=None,
            max_length=255,
            description="Alternative text for accessibility",
            examples=["Front view of La Montera Hotel"]
        )
    ]


# ---------- Output ----------
class ImageOut(BaseModel):
    id: int
    url: Annotated[
        HttpUrl,
        Field(
            description="Full URL of the image",
            examples=["https://cdn.nexovo.com/images/la-montera-front.jpg"]
        )
    ]
    room_id: Annotated[
        Optional[int],
        Field(
            None,
            description="ID of the associated room",
            examples=[101]
        )
    ]
    accommodation_id: Annotated[
        Optional[int],
        Field(
            None,
            description="ID of the associated accommodation",
            examples=[1]
        )
    ]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 10,
                    "url": "https://cdn.nexovo.com/images/la-montera-front.jpg",
                    "room_id": None,
                    "accommodation_id": 1
                }
            ]
        }
    )
