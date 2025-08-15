# app/booking/routes/rooms_router.py
from __future__ import annotations
from json import JSONDecodeError
import json
from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException, Depends, status, Path, Form, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import verify_token
from app.booking.services.image_service import create_image_for_accommodation_from_upload, create_images_for_accommodation_from_keys, delete_images_by_ids
from app.db.session import get_db
from app.common.schemas import ErrorResponse  # ⬅️ nuevo

from app.booking.schemas.room_schema import RoomCreate, RoomOut, RoomUpdate
from app.booking.services.room_service import (
    create_room as service_create_room,
    get_all_rooms,
    get_room,
    get_rooms_by_accommodation_id,
    update_room as service_update_room,
    delete_room as service_delete_room,
)
from app.utils.helpers import _attach_presigned_urls, _parse_delete_ids, _to_str_list, _validate_images_count

router = APIRouter(prefix="/rooms", tags=["Rooms"])

# =========================
#  Config de negocio
# =========================
MAX_IMAGES_PER_ACC = 10         # Máximo total por alojamiento
MAX_FILES_CREATE = 10           # Máximo archivos aceptados al crear


@router.post(
    "/",
    response_model=RoomOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
    description="Creates a new room associated with an accommodation.",
    responses={
        201: {"description": "Created"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
        422: {"description": "Validation error"},
    },
    operation_id="createRoom",
)
def create_room_endpoint(
    payload: str = Form(..., description="Room data in JSON format(String)"),
    images: List[UploadFile] = File(..., description="Images of the room"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    room_in = RoomCreate.model_validate_json(payload)
    _validate_images_count(images)

    room = service_create_room(db, room_in)

    for f in images or []:
        try:
            f.file.seeK(0)
        except Exception as e:
            pass
        create_image_for_accommodation_from_upload(
            f, None, room.id, "rooms", db)

    _attach_presigned_urls(room)

    return room


@router.get(
    "/",
    response_model=List[RoomOut],
    summary="Get all rooms",
    description="Retrieves all rooms from the database.",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
    },
    operation_id="listRooms",
)
def read_all_rooms(db: Session = Depends(get_db)):
    rooms = get_all_rooms(db)
    _attach_presigned_urls(rooms)
    return rooms


@router.get(
    "/{room_id}",
    response_model=RoomOut,
    summary="Get a room by ID",
    description="Retrieves a single room by its unique ID.",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Room not found"},
    },
    operation_id="getRoomById",
)
def read_one_room(
    room_id: int = Path(..., gt=0, description="Room ID"),
    db: Session = Depends(get_db)
):
    room = get_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


@router.get(
    "/by_accommodation/{accommodation_id}",
    response_model=List[RoomOut],
    summary="Get rooms by accommodation ID",
    description="Retrieves all rooms associated with a specific accommodation.",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
    },
    operation_id="getRoomsByAccommodation",
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
    description="Updates the details of a room by its ID.",
    responses={
        200: {"description": "Updated"},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Forbidden (not owner)"},
        404: {"model": ErrorResponse, "description": "Room not found"},
        422: {"description": "Validation error"},
    },
    operation_id="updateRoom",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "updates_json": {"type": "string"},
                            "new_images": {
                                "oneOf": [
                                    {"type": "string", "format": "binary"},
                                    {"type": "array", "items": {
                                        "type": "string", "format": "binary"}},
                                ],
                                "description": "Sube una o varias imágenes."
                            },
                            "delete_image_ids": {"type": "array", "items": {"type": "integer"}},
                            "new_image_keys": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": []
                    },
                    "encoding": {
                        "new_images": {"style": "form", "explode": True},
                        "delete_image_ids": {"style": "form", "explode": True},
                        "new_image_keys": {"style": "form", "explode": True},
                    },
                }
            }
        }
    }
)
async def update_room_endpoint(
    room_id: int = Path(..., gt=0, description="Room ID"),
    updates_json: Optional[str] = Form(
        None, description="Room updates in JSON format"),
    new_images: List[UploadFile] = File(
        None, description="New images for the room"),
    delete_image_ids: Optional[Union[list[int], str]] = Form(
        None, description="Image IDs to delete"),
    new_image_keys: Optional[Union[list[int], str]] = Form(
        None, description="Image keys to delete"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    room = get_room(db, room_id)

    if updates_json:
        try:
            payload = json.loads(updates_json)
        except JSONDecodeError as e:
            raise HTTPException(
                status_code=422,
                detail=f"updates_json is not valid JSON (line {e.lineno}, col {e.colno}): {e.msg}",
            )
        updates = RoomUpdate.model_validate(payload)
        room = service_update_room(db, room_id, updates)

    ids_to_delete = _parse_delete_ids(delete_image_ids)
    keys_to_add = list(dict.fromkeys(_to_str_list(new_image_keys)))

    existing = len(room.images or [])
    final_count = existing - \
        len(ids_to_delete) + \
        (0 if new_images is None else len(new_images)) + len(keys_to_add)
    if final_count > MAX_IMAGES_PER_ACC:
        raise HTTPException(
            status_code=422, detail=f"Max {MAX_IMAGES_PER_ACC} images per rooms")

    if ids_to_delete:
        delete_images_by_ids(db, ids_to_delete, None, room_id)

    for f in new_images or []:
        try:
            f.file.seek(0)
        except Exception:
            pass
        create_image_for_accommodation_from_upload(
            f, None, room_id, "rooms", db)

    if keys_to_add:
        create_images_for_accommodation_from_keys(
            db, None, room_id, keys_to_add)

    room = get_room(db, room_id)
    _attach_presigned_urls(room)
    return room


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a room",
    description="Deletes a room by its ID.",
    response_model=None,
    responses={
        204: {"description": "Deleted. No content."},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Forbidden (not owner)"},
        404: {"model": ErrorResponse, "description": "Room not found"},
    },
    operation_id="deleteRoom",
)
def delete_room_endpoint(
    room_id: int = Path(..., gt=0, description="Room ID"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
) -> None:
    success = service_delete_room(db, room_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
