from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class Room(Base):  # Habitación
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    room_type = Column(String, nullable=False, doc="Tipo de habitación (ej. individual, doble, suite)")
    capacity = Column(Integer, nullable=False, doc="Capacidad máxima de personas")
    amenities = Column(String, doc="Servicios incluidos, separados por comas o como JSON")
    base_price = Column(Float, nullable=False, doc="Precio base por noche")
    is_available = Column(Boolean, default=True, doc="Indica si la habitación está disponible o no")
    beds = Column(Integer, nullable=False, default=1, doc="Cantidad de camas en la habitación")

    accommodation_id = Column(Integer, ForeignKey("accommodations.id"), nullable=False, doc="ID del alojamiento al que pertenece")
    accommodation = relationship("Accommodation", back_populates="rooms")
    images = relationship("Image", back_populates="room", cascade="all, delete")

    availabilities = relationship("Availability", back_populates="room")
