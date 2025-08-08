from pydantic import BaseModel
from typing import Optional, List
from .image_schema import ImageOut  # Asegúrate de tener este archivo creado


class ImageCreate(BaseModel):
    url: str

class RoomCreate(BaseModel):
    room_type: str
    capacity: int
    amenities: Optional[str] = None
    base_price: float
    is_available: Optional[bool] = True
    beds: Optional[int] = 1
    accommodation_id: int
    images: Optional[List[ImageCreate]] = []  # <--- NUEVO

class RoomUpdate(BaseModel):
    room_type: Optional[str] = None
    capacity: Optional[int] = None
    amenities: Optional[str] = None
    base_price: Optional[float] = None
    is_available: Optional[bool] = None
    beds: Optional[int] = None
    accommodation_id: Optional[int] = None

class RoomOut(BaseModel):
    id: int
    room_type: str
    capacity: int
    amenities: Optional[str] = None
    base_price: float
    is_available: bool
    beds: int
    accommodation_id: int
    images: List[ImageOut] = []  # Nueva relación incluida

    class Config:
        orm_mode = True
