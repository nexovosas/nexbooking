from sqlalchemy.orm import Session
from app.booking.models.image_model import Image
from app.booking.schemas.image_schema import ImageCreate

def create_image_for_accommodation(db: Session, image_data: ImageCreate, accommodation_id: int):
    db_image = Image(
        url=image_data.url,
        alt_text=image_data.alt_text,
        accommodation_id=accommodation_id
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def create_images(db: Session, image_data: list[ImageCreate], room_id: int = None, accommodation_id: int = None):
    images = []
    for img in image_data:
        image = Image(url=img.url, room_id=room_id, accommodation_id=accommodation_id)
        db.add(image)
        images.append(image)
    db.commit()
    return images