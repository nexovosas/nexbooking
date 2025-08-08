from pydantic import BaseModel
import datetime
from typing import Optional

# Base para reutilizar
class AvailabilityBase(BaseModel):
    date: datetime.date
    price: float
    room_id: int

# Para crear
class AvailabilityCreate(AvailabilityBase):
    pass

# Para actualizar
class AvailabilityUpdate(BaseModel):
    date: Optional[datetime.date] = None
    price: Optional[float] = None

# Para mostrar
class AvailabilityOut(AvailabilityBase):
    id: int

    class Config:
        orm_mode = True
