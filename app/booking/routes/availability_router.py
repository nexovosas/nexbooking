from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.auth import verify_token
from app.booking.schemas.availability_schema import *
from app.booking.services.availability_service import *
from app.db.session import get_db

router = APIRouter( tags=["Availabilities"])

# Crear disponibilidad
@router.post("/", response_model=AvailabilityOut)
def create_availability_route(
    availability: AvailabilityCreate,
    db: Session = Depends(get_db), 
    _: dict = Depends(verify_token)
):
    return create_availability(db, availability)

# Obtener disponibilidades por habitación
@router.get("/room/{room_id}", response_model=List[AvailabilityOut])
def get_availabilities_by_room_route(
    room_id: int,
    db: Session = Depends(get_db)
):
    return get_availabilities_by_room(db, room_id)

# Obtener una disponibilidad por ID
@router.get("/{availability_id}", response_model=AvailabilityOut)
def get_availability_by_id_route(
    availability_id: int,
    db: Session = Depends(get_db)
):
    availability = get_availability_by_id(db, availability_id)
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    return availability

# Actualizar una disponibilidad
@router.put("/{availability_id}", response_model=AvailabilityOut)
def update_availability_route(
    availability_id: int,
    availability_data: AvailabilityUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    updated = update_availability(db, availability_id, availability_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Availability not found")
    return updated

# Eliminar disponibilidad
@router.delete("/{availability_id}")
def delete_availability_route(
    availability_id: int,
    db: Session = Depends(get_db),
      _: dict = Depends(verify_token)
):
    deleted = delete_availability(db, availability_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Availability not found")
    return {"message": "Availability deleted"}
