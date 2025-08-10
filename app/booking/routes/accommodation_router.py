from __future__ import annotations
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import verify_token
from app.db.session import get_db
from app.common.schemas import ErrorResponse

from app.booking.schemas.accommodation_schema import (
    AccommodationCreate,
    AccommodationOut,
    AccommodationUpdate,
)
from app.booking.services.accommodation_service import (
    create_accommodation,
    get_all_accommodations,
    update_accommodation,
    delete_accommodation,
    get_accommodations_by_host,
    search_accommodations_service,
    get_accommodation,
)

router = APIRouter(tags=["Accommodations"], prefix="/accommodations")

@router.post(
    "/",
    response_model=AccommodationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new accommodation",
    description="Creates a new accommodation and optionally its images.",
    responses={
        201: {"description": "Created"},
        400: {"model": ErrorResponse, "description": "Invalid input or business rule violation"},
        401: {"model": ErrorResponse},
        409: {"model": ErrorResponse, "description": "Conflict (e.g., duplicate name)"},
        422: {"description": "Validation error"},
    },
    operation_id="createAccommodation",
)
def create_accommodation_endpoint(
    accommodation_data: AccommodationCreate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    # host_id SIEMPRE del JWT (Django)
    return create_accommodation(db=db, accommodation_data=accommodation_data, host_id=user_data["id"])

@router.get(
    "/",
    response_model=List[AccommodationOut],
    summary="List all accommodations",
    description="Retrieves all accommodations with optional pagination.",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse},
    },
    operation_id="listAccommodations",
)
def read_all_accommodations(db: Session = Depends(get_db)):
    return get_all_accommodations(db)

@router.put(
    "/{accommodation_id}",
    response_model=AccommodationOut,
    summary="Update an existing accommodation",
    description="Updates fields of an accommodation. Requires authentication.",
    responses={
        200: {"description": "Updated"},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Forbidden (not owner)"},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
        422: {"description": "Validation error"},
    },
    operation_id="updateAccommodation",
)
def update_accommodation_endpoint(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    hospedaje: AccommodationUpdate = ...,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    acc = get_accommodation(db, accommodation_id)  # lanza 404 si no existe
    if acc.host_id != user_data["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    updated = update_accommodation(db, accommodation_id, hospedaje)
    return updated

@router.delete(
    "/{accommodation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an accommodation",
    description="Deletes an accommodation by its ID. Requires authentication.",
    response_model=None,
    responses={
        204: {"description": "Deleted. No content."},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Forbidden (not owner)"},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
    },
    operation_id="deleteAccommodation",
)
def delete_accommodation_endpoint(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
) -> None:
    acc = get_accommodation(db, accommodation_id)  # 404 si no existe
    if acc.host_id != user_data["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    delete_accommodation(db, accommodation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get(
    "/my",
    response_model=List[AccommodationOut],
    summary="Get accommodations owned by authenticated host",
    description="Returns accommodations owned by the authenticated host.",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse},
    },
    operation_id="listMyAccommodations",
)
def get_my_accommodations(
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    return get_accommodations_by_host(db, user_data.get("id"))

@router.get(
    "/search",
    response_model=List[AccommodationOut],
    summary="Search accommodations with filters",
    description="Searches accommodations by name, max price, and services.",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse},
    },
    operation_id="searchAccommodations",
)
def search_accommodations(
    name: Optional[str] = Query("", description="Filter by name"),
    max_price: Optional[float] = Query(99999.0, gt=0, description="Maximum price"),
    services: Optional[str] = Query("", description="Comma-separated list of services"),
    db: Session = Depends(get_db)
):
    return search_accommodations_service(db, name, max_price, services)

@router.get(
    "/{accommodation_id}",
    response_model=AccommodationOut,
    summary="Retrieve an accommodation by ID",
    description="Fetches a single accommodation by its unique ID.",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
    },
    operation_id="getAccommodationById",
)
def read_one_accommodation(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db)
):
    db_accommodation = get_accommodation(db, accommodation_id)
    if not db_accommodation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    return db_accommodation
