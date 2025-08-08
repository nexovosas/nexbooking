from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class Accommodation(Base):  # Hospedaje
    __tablename__ = "accommodations"

    id = Column(Integer, primary_key=True)  # ID único del hospedaje
    name = Column(String, nullable=False)  # Nombre del hospedaje
    location = Column(String, nullable=False)  # Ubicación del hospedaje (ciudad, zona, etc.)
    description = Column(Text)  # Descripción general del hospedaje
    services = Column(String, nullable=True)  # Servicios ofrecidos, por ejemplo: "wifi, tv, cocina"
    host_id = Column(Integer, ForeignKey("user.id"), nullable=False)  # ID del usuario que ofrece el hospedaje
    pet_friendly = Column(Boolean, default=False)  # Indica si se permiten mascotas
    type = Column(String, nullable=False,default="-")  # Tipo de hospedaje (hotel, cabaña, hostal, etc.)
    is_active = Column(Boolean, default=True, nullable=False)  #  Activado/desactivado (por defecto activado)
    # Agrega al final del modelo Accommodation:
    images = relationship("Image", back_populates="accommodation", cascade="all, delete")

    host = relationship("User", backref="accommodations")  # Relación con el anfitrión (usuario propietario)
    rooms = relationship("Room", back_populates="accommodation")  # Relación con las habitaciones asociadas al hospedaje

