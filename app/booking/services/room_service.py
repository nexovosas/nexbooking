from sqlalchemy.orm import Session
from app.booking.models.room_model import Room
from app.booking.schemas.room_schema import RoomCreate, RoomUpdate
from app.booking.services.image_service import create_images  # <-- nuevo

def create_room(db: Session, room_data: RoomCreate) -> Room:
    images_data = room_data.images
    room_dict = room_data.dict(exclude={"images"})  # Excluye imágenes del dict principal

    new_room = Room(**room_dict)
    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    # Crea las imágenes asociadas a la habitación
    if images_data:
        create_images(db=db, image_data=images_data, room_id=new_room.id)

    return new_room

def get_room(db: Session, room_id: int) -> Room | None:
    return db.query(Room).filter(Room.id == room_id).first()

def get_all_rooms(db: Session) -> list[Room]:
    return db.query(Room).all()

def get_rooms_by_accommodation_id(db: Session, accommodation_id: int) -> list[Room]:
    return db.query(Room).filter(Room.accommodation_id == accommodation_id).all()

def update_room(db: Session, room_id: int, room_data: RoomUpdate) -> Room | None:
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        return None

    for field, value in room_data.dict(exclude_unset=True).items():
        setattr(db_room, field, value)

    db.commit()
    db.refresh(db_room)
    return db_room

def delete_room(db: Session, room_id: int) -> bool:
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        return False

    db.delete(db_room)
    db.commit()
    return True
