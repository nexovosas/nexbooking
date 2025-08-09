# app/booking/models/room.py
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    room_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, doc="Tipo de habitación (ej. individual, doble, suite)")
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, doc="Capacidad máxima de personas")
    amenities: Mapped[str | None] = mapped_column(String(255), doc="Servicios incluidos, separados por comas o como JSON")
    base_price: Mapped[float] = mapped_column(Float, nullable=False, doc="Precio base por noche")
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", doc="Indica si la habitación está disponible o no")
    beds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1", doc="Cantidad de camas en la habitación")

    accommodation_id: Mapped[int] = mapped_column(
        ForeignKey("accommodations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID del alojamiento al que pertenece"
    )

    # Relaciones
    accommodation = relationship("Accommodation", back_populates="rooms")
    images = relationship("Image", back_populates="room", cascade="all, delete-orphan")
    availabilities = relationship("Availability", back_populates="room")

    __table_args__ = (
        # No dos habitaciones con el mismo nombre/tipo en un mismo alojamiento
        UniqueConstraint("accommodation_id", "room_type", name="uq_rooms_accommodation_room_type"),
        # Capacidad y precio siempre positivos
        CheckConstraint("capacity > 0", name="ck_rooms_capacity_positive"),
        CheckConstraint("beds > 0", name="ck_rooms_beds_positive"),
        CheckConstraint("base_price >= 0", name="ck_rooms_base_price_non_negative"),
        # Índice para consultas por alojamiento y disponibilidad
        Index("ix_rooms_accommodation_available", "accommodation_id", "is_available"),
    )
