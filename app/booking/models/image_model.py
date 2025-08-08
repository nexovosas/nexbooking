from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False, doc="URL de la imagen")

    # Opcional: nombre alternativo o descripción
    alt_text = Column(String, nullable=True)

    # Relación polimórfica
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    accommodation_id = Column(Integer, ForeignKey("accommodations.id"), nullable=True)

    room = relationship("Room", back_populates="images")
    accommodation = relationship("Accommodation", back_populates="images")
