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
        Field(
            description="URL of the image",
            examples=["https://cdn.nexovo.com/images/la-montera-front.jpg"]
        )
    ]
    alt_text: Annotated[
        Optional[str],
        Field(
            None,
            max_length=255,
            description="Alternative text for the image",
            examples=["Front view of the hotel"]
        )
    ]


# ---------- Accommodation Create ----------
class AccommodationCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "name": "La Montera Hotel",
                "location": "San Vicente Ferrer, Antioquia",
                "description": "5-star hilltop hotel with 360° views, glamping area, spa, and helipad.",
                "services": "glamping,spa,helicopter-pad,paragliding",
                "pet_friendly": True,
                "type": "Hotel",
                "is_active": True,
                
            }
        ]
    })
    name: Annotated[str, Field(min_length=2, max_length=150, examples=["La Montera Hotel"])]
    location: Annotated[str, Field(min_length=2, max_length=150, examples=["San Vicente Ferrer, Antioquia"])]
    description: Annotated[Optional[str], Field(None, max_length=500, examples=["5-star hilltop hotel with 360° views."])]
    services: Annotated[Optional[str], Field(None, max_length=300, examples=["glamping,spa,helicopter-pad"])]
    pet_friendly: Annotated[bool, Field(default=False, examples=[True])]
    type: Annotated[str, Field(min_length=2, max_length=50, examples=["Hotel"])]
    is_active: Annotated[bool, Field(default=True, examples=[True])]
    


# ---------- Accommodation Update ----------
class AccommodationUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "name": "La Montera Glamping",
                "description": "Updated description for the glamping site",
                "services": "glamping,spa",
                "is_active": False
            }
        ]
    })
    name: Annotated[Optional[str], Field(None, min_length=2, max_length=150)]
    location: Annotated[Optional[str], Field(None, min_length=2, max_length=150)]
    description: Annotated[Optional[str], Field(None, max_length=500)]
    services: Annotated[Optional[str], Field(None, max_length=300)]
    pet_friendly: Optional[bool] = None
    type: Annotated[Optional[str], Field(None, min_length=2, max_length=50)]
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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "La Montera Hotel",
                    "location": "San Vicente Ferrer, Antioquia",
                    "description": "5-star hilltop hotel with 360° views, glamping, spa, and helipad.",
                    "services": "glamping,spa,helicopter-pad,paragliding",
                    "pet_friendly": True,
                    "type": "Hotel",
                    "host_id": 1,
                    "is_active": True,
                    "rooms": [],
                    "images": [
                        {
                            "url": "https://cdn.nexovo.com/images/la-montera-front.jpg",
                            "alt_text": "Front view of La Montera Hotel"
                        }
                    ]
                }
            ]
        }
    )
