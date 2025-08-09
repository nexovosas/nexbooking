# app/booking/routes/accommodation_router.py
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import verify_token
from app.db.session import get_db
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
)
def create_accommodation(
    accommodation_data: AccommodationCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    return create_accommodation(db=db, accommodation_data=accommodation_data)


@router.get("/", response_model=List[AccommodationOut], summary="List all accommodations")
def read_all_accommodations(db: Session = Depends(get_db)):
    return get_all_accommodations(db)


@router.put("/{accommodation_id}", response_model=AccommodationOut, summary="Update an existing accommodation")
def update_accommodation(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    hospedaje: AccommodationUpdate = ...,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    updated = update_accommodation(db, accommodation_id, hospedaje)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    return updated


@router.delete(
    "/{accommodation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an accommodation",
    response_model=None,
)
def delete_accommodation(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
) -> None:
    success = delete_accommodation(db, accommodation_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/my", response_model=List[AccommodationOut], summary="Get accommodations owned by authenticated host")
def get_my_accommodations(
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    return get_accommodations_by_host(db, user_data.get("id"))


@router.get("/search", response_model=List[AccommodationOut], summary="Search accommodations with filters")
def search_accommodations(
    name: Optional[str] = Query("", description="Filter by name"),
    max_price: Optional[float] = Query(99999.0, gt=0, description="Maximum price"),
    services: Optional[str] = Query("", description="Comma-separated list of services"),
    db: Session = Depends(get_db)
):
    return search_accommodations_service(db, name, max_price, services)


@router.get("/{accommodation_id}", response_model=AccommodationOut, summary="Retrieve an accommodation by ID")
def read_one_accommodation(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db)
):
    db_accommodation = get_accommodation(db, accommodation_id)
    if not db_accommodation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    return db_accommodation
