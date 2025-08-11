# app/booking/models/accommodation.py
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Accommodation(Base):
    __tablename__ = "accommodations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text())
    services: Mapped[str | None] = mapped_column(String(255))

    host_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),  # <-- con schema
        nullable=False,
        index=True,
    )
    
    # Metadatos
    pet_friendly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="-")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    # Relaciones ORM (asumiendo que tienes un modelo User mapeado; si no, puedes quitar esta línea)
    host = relationship("User", backref="accommodations")
    rooms = relationship("Room", back_populates="accommodation", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="accommodation", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("host_id", "name", "location", name="uq_accommodations_host_name_location"),
        Index("ix_accommodations_location_name", "location", "name"),
    )
