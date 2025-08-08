from pydantic import BaseModel
from typing import Optional, List
from .room_schema import RoomOut
from .image_schema import ImageOut


class ImageCreate(BaseModel):
    url: str
    alt_text: Optional[str] = None

class AccommodationCreate(BaseModel):
    name: str
    location: str
    description: Optional[str] = None
    services: Optional[str] = None
    pet_friendly: Optional[bool] = False
    type: str
    host_id: int
    is_active: Optional[bool] = True
    images: Optional[List[ImageCreate]] = None  # 👈 Agregado


# Schema para actualizar parcialmente un hospedaje
class AccommodationUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    services: Optional[str] = None
    pet_friendly: Optional[bool] = None
    type: Optional[str] = None
    host_id: Optional[int] = None
    is_active: Optional[bool] = None


# Schema para devolver un hospedaje como respuesta
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
    rooms: List[RoomOut] = []              # ✅ Relación con habitaciones
    images: List[ImageOut] = []            # ✅ Relación con imágenes

    class Config:
        orm_mode = True
