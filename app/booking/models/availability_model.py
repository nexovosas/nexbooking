# app/booking/models/availability_model.py

from sqlalchemy import Column, Integer, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
#Disponibilidad 
class Availability(Base): 
    __tablename__ = "availabilities"

    id = Column(Integer, primary_key=True, index=True)
    
    # Fecha en la que la habitación está disponible
    date = Column(Date, nullable=False)
    
    # Precio por esa fecha específica
    price = Column(Float, nullable=False)
    
    # Relación con la habitación correspondiente
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    room = relationship("Room", back_populates="availabilities")
