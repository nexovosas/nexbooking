from pydantic import BaseModel
from typing import Optional
from datetime import date

class BookingBase(BaseModel):
    check_in: date
    check_out: date
    property_id: int  # FK
    guest_id: int     # FK (usuario que hace la reserva)

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: int

    class Config:
        orm_mode = True
