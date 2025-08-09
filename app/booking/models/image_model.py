# app/booking/models/image.py
from sqlalchemy import Integer, String, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    url: Mapped[str] = mapped_column(String(500), nullable=False, doc="URL de la imagen")
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True, doc="Texto alternativo o descripción")

    room_id: Mapped[int | None] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    accommodation_id: Mapped[int | None] = mapped_column(
        ForeignKey("accommodations.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    room = relationship("Room", back_populates="images")
    accommodation = relationship("Accommodation", back_populates="images")

    __table_args__ = (
        CheckConstraint("length(url) > 0", name="ck_image_url_not_empty"),
        Index("ix_image_room", "room_id"),
        Index("ix_image_accommodation", "accommodation_id"),
    )
