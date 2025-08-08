from pydantic import BaseModel, Field,model_validator
from datetime import date
from typing import Optional
from enum import Enum

# 🔹 Esquema para reporte de ganancias (valor retornado)
class EarningsReport(BaseModel):
    total_earnings: float

class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


# 🔹 Base común para reutilizar campos
class BookingBase(BaseModel):
    user_id: int
    room_id: int
    start_date: date
    end_date: date
    guests: int = Field(..., ge=1, description="Debe haber al menos 1 huésped")


# 🔹 Para crear una nueva reserva
class BookingCreate(BookingBase):
    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("La fecha de salida debe ser posterior a la de entrada")
        return self


# 🔹 Para actualizar una reserva existente (todos los campos opcionales)
class BookingUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    guests: Optional[int] = Field(None, ge=1)
    status: Optional[BookingStatus] = None  # <--- editable aquí también


# 🔹 Para mostrar datos de una reserva id,status, and code 
class BookingOut(BookingBase):
    id: int
    status: BookingStatus
    code: str  # ahora también mostramos el código
    total_price: float  # 💰 Total a pagar por la reserva

    class Config:
        orm_mode = True



