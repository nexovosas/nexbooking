from __future__ import annotations
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Path, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.verify_token import verify_token  # normalized user dict with "id" and "role"
from app.booking.services.image_service import create_image_for_accommodation_from_upload
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
    description="Creates a new accommodation and optionally its images. Requires authentication.",
    responses={
        201: {"description": "Created"},
        400: {"model": ErrorResponse, "description": "Invalid input or business rule violation"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Conflict (e.g., duplicate name)"},
        422: {"description": "Validation error"},
    },
    operation_id="createAccommodation",
)
def create_accommodation_endpoint(
    payload: AccommodationCreate = Form(..., description="Accommodation data in JSON format"),
    images: List[UploadFile] = File(..., description="List of images for the accommodation"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    data = json.loads(payload)
    acc_in = AccommodationCreate(**data)  # asegúrate de quitar 'images' del schema si ya no lo usas
    acc = create_accommodation(db, acc_in, host_id=user["id"])

    for f in images or []:
        create_image_for_accommodation_from_upload(f, acc.id, db)

    return acc


@router.get(
    "/",
    response_model=List[AccommodationOut],
    summary="List all accommodations",
    description="Retrieves all accommodations with optional pagination.",
    responses={
        200: {"description": "Successful response"},
    },
    operation_id="listAccommodations",
)
def read_all_accommodations(db: Session = Depends(get_db)):
    return get_all_accommodations(db)

@router.get(
    "/my",
    response_model=List[AccommodationOut],
    summary="Get accommodations owned by authenticated host",
    description="Returns accommodations owned by the authenticated host.",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
    operation_id="listMyAccommodations",
)
def get_my_accommodations(
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    host_id = user.get("id")
    if host_id is None:
        raise HTTPException(status_code=401, detail="Invalid token: user id missing")
    return get_accommodations_by_host(db, host_id)

@router.get(
    "/search",
    response_model=List[AccommodationOut],
    summary="Search accommodations with filters",
    description="Searches accommodations by name, max price, and services.",
    responses={200: {"description": "Successful response"}},
    operation_id="searchAccommodations",
)
def search_accommodations(
    name: Optional[str] = Query(None, description="Filter by name"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    services: Optional[str] = Query(None, description="Comma-separated list of services"),
    db: Session = Depends(get_db),
):
    return search_accommodations_service(db, name, max_price, services)

@router.get(
    "/{accommodation_id}",
    response_model=AccommodationOut,
    summary="Retrieve an accommodation by ID",
    description="Fetches a single accommodation by its unique ID.",
    responses={
        200: {"description": "Successful response"},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
    },
    operation_id="getAccommodationById",
)
def read_one_accommodation(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db),
):
    db_accommodation = get_accommodation(db, accommodation_id)
    return db_accommodation


@router.put(
    "/{accommodation_id}",
    response_model=AccommodationOut,
    summary="Update an existing accommodation",
    description="Updates fields of an accommodation. Requires authentication and ownership.",
    responses={
        200: {"description": "Updated"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden (not owner)"},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
        422: {"description": "Validation error"},
    },
    operation_id="updateAccommodation",
)
def update_accommodation_endpoint(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    updates: AccommodationUpdate = ...,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    acc = get_accommodation(db, accommodation_id)  # raises 404 if not found
    if acc.host_id != user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return update_accommodation(db, accommodation_id, updates)


@router.delete(
    "/{accommodation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an accommodation",
    description="Deletes an accommodation by its ID. Requires authentication and ownership.",
    response_model=None,
    responses={
        204: {"description": "Deleted. No content."},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden (not owner)"},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
    },
    operation_id="deleteAccommodation",
)
def delete_accommodation_endpoint(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
) -> Response:
    acc = get_accommodation(db, accommodation_id)  # raises 404 if not found
    if acc.host_id != user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    delete_accommodation(db, accommodation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
