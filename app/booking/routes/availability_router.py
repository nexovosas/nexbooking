# app/booking/routes/availability_router.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import verify_token
from app.booking.schemas.availability_schema import (
    AvailabilityCreate,
    AvailabilityOut,
    AvailabilityUpdate,
)
from app.booking.services.availability_service import (
    create_availability,
    get_availabilities_by_room,
    get_availability_by_id,
    update_availability,
    delete_availability,
)
from app.db.session import get_db
from app.common.schemas import ErrorResponse  # ⬅️ nuevo

router = APIRouter(tags=["Availability"], prefix="/availability")


@router.post(
    "/",
    response_model=AvailabilityOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear disponibilidad",
    description="Crea una nueva disponibilidad para una habitación específica.",
    responses={
        201: {"description": "Creado"},
        400: {"model": ErrorResponse, "description": "Regla de negocio o datos inválidos"},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Habitación/Alojamiento no encontrado"},
        422: {"description": "Error de validación"},
    },
    operation_id="createAvailability",
)
def create_availability_route(
    availability: AvailabilityCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    return create_availability(db, availability)


@router.get(
    "/room/{room_id}",
    response_model=List[AvailabilityOut],
    summary="Listar disponibilidades por habitación",
    description="Devuelve todas las disponibilidades asociadas a una habitación.",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Habitación no encontrada"},
    },
    operation_id="listAvailabilityByRoom",
)
def get_availabilities_by_room_route(
    room_id: int = Path(..., ge=1, description="ID de la habitación"),
    db: Session = Depends(get_db)
):
    return get_availabilities_by_room(db, room_id)


@router.get(
    "/{availability_id}",
    response_model=AvailabilityOut,
    summary="Obtener disponibilidad por ID",
    description="Devuelve los datos de una disponibilidad específica.",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Disponibilidad no encontrada"},
    },
    operation_id="getAvailabilityById",
)
def get_availability_by_id_route(
    availability_id: int = Path(..., ge=1, description="ID de la disponibilidad"),
    db: Session = Depends(get_db)
):
    availability = get_availability_by_id(db, availability_id)
    if not availability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    return availability


@router.put(
    "/{availability_id}",
    response_model=AvailabilityOut,
    summary="Actualizar disponibilidad",
    description="Actualiza los datos de una disponibilidad existente.",
    responses={
        200: {"description": "Actualizado"},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Prohibido (no propietario)"},
        404: {"model": ErrorResponse, "description": "Disponibilidad no encontrada"},
        422: {"description": "Error de validación"},
    },
    operation_id="updateAvailability",
)
def update_availability_route(
    availability_id: int = Path(..., ge=1, description="ID de la disponibilidad"),
    availability_data: AvailabilityUpdate = ...,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    updated = update_availability(db, availability_id, availability_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    return updated


@router.delete(
    "/{availability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar disponibilidad",
    description="Elimina una disponibilidad de la base de datos.",
    response_model=None,
    responses={
        204: {"description": "Eliminado. Sin contenido."},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Prohibido (no propietario)"},
        404: {"model": ErrorResponse, "description": "Disponibilidad no encontrada"},
    },
    operation_id="deleteAvailability",
)
def delete_availability_route(
    availability_id: int = Path(..., ge=1, description="ID de la disponibilidad"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
) -> None:
    deleted = delete_availability(db, availability_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
