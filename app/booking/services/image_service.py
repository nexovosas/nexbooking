# app/booking/services/image_service.py
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.booking.models.image_model import Image
from app.booking.schemas.image_schema import ImageCreate


def create_image_for_accommodation(
    db: Session, image_data: ImageCreate, accommodation_id: int
) -> Image:
    """
    Create a single image entry for an accommodation.
    """
    db_image = Image(
        url=image_data.url,
        alt_text=image_data.alt_text,
        accommodation_id=accommodation_id,
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def create_images(
    db: Session,
    image_data: List[ImageCreate],
    room_id: Optional[int] = None,
    accommodation_id: Optional[int] = None,
) -> List[Image]:
    """
    Create multiple images for either a room or an accommodation.
    """
    if not room_id and not accommodation_id:
        raise ValueError("Either 'room_id' or 'accommodation_id' must be provided.")

    images: List[Image] = []
    for img in image_data:
        new_image = Image(
            url=img.url,
            alt_text=img.alt_text,
            room_id=room_id,
            accommodation_id=accommodation_id,
        )
        db.add(new_image)
        images.append(new_image)

    db.commit()
    for image in images:
        db.refresh(image)

    return images
