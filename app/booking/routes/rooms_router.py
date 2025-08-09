# app/booking/routes/rooms_router.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Path
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import verify_token
from app.db.session import get_db
from app.booking.schemas.room_schema import RoomCreate, RoomOut, RoomUpdate
from app.booking.services.room_service import (
    create_room as service_create_room,
    get_all_rooms,
    get_room,
    get_rooms_by_accommodation_id,
    update_room as service_update_room,
    delete_room as service_delete_room,
)

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post(
    "/",
    response_model=RoomOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
    description="Creates a new room associated with an accommodation."
)
def create_room_endpoint(
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    return service_create_room(db=db, room_data=room_data)


@router.get(
    "/",
    response_model=List[RoomOut],
    summary="Get all rooms",
    description="Retrieves all rooms from the database."
)
def read_all_rooms(db: Session = Depends(get_db)):
    return get_all_rooms(db)


@router.get(
    "/{room_id}",
    response_model=RoomOut,
    summary="Get a room by ID",
    description="Retrieves a single room by its unique ID."
)
def read_one_room(
    room_id: int = Path(..., gt=0, description="Room ID"),
    db: Session = Depends(get_db)
):
    room = get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


@router.get(
    "/by_accommodation/{accommodation_id}",
    response_model=List[RoomOut],
    summary="Get rooms by accommodation ID",
    description="Retrieves all rooms associated with a specific accommodation."
)
def read_rooms_by_accommodation(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db)
):
    return get_rooms_by_accommodation_id(db, accommodation_id)


@router.put(
    "/{room_id}",
    response_model=RoomOut,
    summary="Update a room",
    description="Updates the details of a room by its ID."
)
def update_room_endpoint(
    room_id: int = Path(..., gt=0, description="Room ID"),
    room_data: RoomUpdate = ...,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    updated_room = service_update_room(db, room_id, room_data)
    if not updated_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return updated_room


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a room",
    description="Deletes a room by its ID.",
    response_model=None,
)
def delete_room_endpoint(
    room_id: int = Path(..., gt=0, description="Room ID"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
) -> None:
    success = service_delete_room(db, room_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
