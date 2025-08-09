# app/booking/models/booking.py
from datetime import date, datetime
from sqlalchemy import (
    Integer, Date, Enum, Float, String,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum


class BookingStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),  # Cambia a "users.id" si tu tabla se llama así
        nullable=False,
        index=True
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    guests: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        nullable=False,
        server_default=BookingStatus.pending.value
    )

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    # Relaciones
    user = relationship("User", backref="bookings")
    room = relationship("Room", backref="bookings")

    __table_args__ = (
        # Asegurar que la fecha de fin sea posterior a la de inicio
        CheckConstraint("end_date > start_date", name="ck_booking_dates_valid"),
        # Cantidad de huéspedes positiva
        CheckConstraint("guests > 0", name="ck_booking_guests_positive"),
        # Precio positivo
        CheckConstraint("total_price > 0", name="ck_booking_price_positive"),
        # Evitar solapamiento exacto del mismo código (el code ya es unique, esto refuerza)
        UniqueConstraint("code", name="uq_booking_code"),
        # Índice para búsquedas rápidas por rango de fechas y habitación
        Index("ix_booking_room_dates", "room_id", "start_date", "end_date"),
    )
