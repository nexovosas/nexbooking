from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.auth import verify_token
from app.db.session import get_db

from app.booking.schemas.room_schema import *
from app.booking.services.room_service import *

router = APIRouter(tags=["Rooms"])

@router.post("/", response_model=RoomOut)
def create_room(room_data: RoomCreate, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    return create_room(db=db, room_data=room_data)


@router.get("/", response_model=List[RoomOut])
def read_all(db: Session = Depends(get_db)):
    return get_all_rooms(db)

@router.get("/{room_id}", response_model=RoomOut)
def read_one_room(room_id: int, db: Session = Depends(get_db)):
    db_room = get_room(db, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    return db_room

@router.get("/by_accommodation/{accommodation_id}", response_model=List[RoomOut])
def read_by_accommodation(accommodation_id: int, db: Session = Depends(get_db)):
    return get_rooms_by_accommodation_id(db, accommodation_id)

@router.put("/{room_id}", response_model=RoomOut)
def update_room(room_id: int, room_data: RoomUpdate, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    updated = update_room(db, room_id, room_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Room not found")
    return updated

@router.delete("/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    success = delete_room(db, room_id)
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"detail": "Room deleted successfully"}


