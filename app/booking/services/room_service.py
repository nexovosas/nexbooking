# app/booking/services/room_service.py
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.booking.models.room_model import Room
from app.booking.schemas.room_schema import RoomCreate, RoomUpdate
from app.booking.services.image_service import create_images


def create_room(db: Session, room_data: RoomCreate) -> Room:
    """
    Create a new room and optionally attach images to it.
    """
    images_data = room_data.images or []
    room_dict = room_data.model_dump(exclude={"images"})  # Pydantic v2

    new_room = Room(**room_dict)
    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    if images_data:
        create_images(db=db, image_data=images_data, room_id=new_room.id)

    return new_room


def get_room(db: Session, room_id: int) -> Optional[Room]:
    """
    Retrieve a room by its ID.
    """
    return db.query(Room).filter(Room.id == room_id).first()


def get_all_rooms(db: Session) -> List[Room]:
    """
    Retrieve all rooms.
    """
    return db.query(Room).all()


def get_rooms_by_accommodation_id(db: Session, accommodation_id: int) -> List[Room]:
    """
    Retrieve all rooms belonging to a specific accommodation.
    """
    return (
        db.query(Room)
        .filter(Room.accommodation_id == accommodation_id)
        .all()
    )


def update_room(db: Session, room_id: int, room_data: RoomUpdate) -> Optional[Room]:
    """
    Update an existing room.
    """
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        return None

    for field, value in room_data.model_dump(exclude_unset=True).items():
        setattr(db_room, field, value)

    db.commit()
    db.refresh(db_room)
    return db_room


def delete_room(db: Session, room_id: int) -> bool:
    """
    Delete a room by ID.
    """
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        return False

    db.delete(db_room)
    db.commit()
    return True
