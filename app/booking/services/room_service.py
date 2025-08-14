# app/booking/services/room_service.py
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.booking.models.room_model import Room
from app.booking.schemas.room_schema import RoomCreate, RoomUpdate
from app.booking.services.image_service import create_image_for_rooms_from_upload
from app.booking.services.s3_service import S3Service


def create_room(db: Session, room_data: RoomCreate) -> Room:
    """
    Create a new room and optionally attach images to it.
    """
    
    payload = room_data.model_dump(exclude={"images"})  # Pydantic v2
    payload.pop("images", None)  # Eliminar imágenes del dict

    new_room = Room(**payload)
    db.add(new_room)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "foreign key" in msg or "fk" in msg:
            raise HTTPException(status_code=404, detail="Host not found (foreign key).")
        if "unique" in msg:
            raise HTTPException(status_code=409, detail="Unique constraint violated (id).")
        raise HTTPException(status_code=409, detail="Integrity error.")
    db.refresh(new_room)
    
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
    room = get_room(db, room_id)
    
    s3 = S3Service()
    s3.delete_objects(f"rooms/{room_id}")

    db.delete(room)
    db.commit()
    return True
