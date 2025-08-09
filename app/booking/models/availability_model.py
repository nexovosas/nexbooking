# app/booking/models/availability.py
from datetime import date
from sqlalchemy import Integer, Date, Float, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Availability(Base):
    __tablename__ = "availabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True, doc="Fecha específica de disponibilidad")
    price: Mapped[float] = mapped_column(Float, nullable=False, doc="Precio para esa fecha")

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID de la habitación correspondiente"
    )

    # Relaciones
    room = relationship("Room", back_populates="availabilities")

    __table_args__ = (
        # Evita dos registros para la misma habitación y fecha
        UniqueConstraint("room_id", "date", name="uq_availability_room_date"),
        # Precio positivo
        CheckConstraint("price > 0", name="ck_availability_price_positive"),
        # Índice compuesto para búsqueda por habitación + fecha
        Index("ix_availability_room_date", "room_id", "date"),
    )
