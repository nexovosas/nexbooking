from __future__ import annotations

from datetime import date
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import verify_token
from app.db.session import get_db
from app.common.schemas import ErrorResponse  # ⬅️ nuevo

from app.booking.schemas.booking_schema import (
    BookingOut,
    BookingCreate,
    BookingUpdate,
    EarningsReport,
)
from app.booking.services.booking_service import (
    get_income_by_accommodation,
    get_all_bookings,
    create_booking,
    update_booking,
    delete_booking,
    get_bookings_by_host,
    get_earnings_by_host_and_dates,
    get_bookings_grouped_by_period,
    get_booking_by_id,
)

router = APIRouter(tags=["Bookings"], prefix="/bookings")


@router.get(
    "/income",
    summary="Obtener ingresos totales por alojamiento",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
    },
    operation_id="getIncomeByAccommodation",
)
def income_report(db: Session = Depends(get_db)) -> dict:
    return get_income_by_accommodation(db)


@router.get(
    "/",
    response_model=List[BookingOut],
    summary="Listar todas las reservas",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
    },
    operation_id="listBookings",
)
def list_bookings(db: Session = Depends(get_db)) -> List[BookingOut]:
    return get_all_bookings(db)


@router.post(
    "/",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva reserva",
    responses={
        201: {"description": "Creado"},
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "No autorizado"},
        422: {"description": "Error de validación"},
    },
    operation_id="createBooking",
)
async def create_new_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token),
) -> BookingOut:
    email = user_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not found in token",
        )
    return await create_booking(db, booking, user_email=email)


@router.put(
    "/{booking_id}",
    response_model=BookingOut,
    summary="Actualizar reserva",
    responses={
        200: {"description": "Actualizado"},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Prohibido"},
        404: {"model": ErrorResponse, "description": "Reserva no encontrada"},
        422: {"description": "Error de validación"},
    },
    operation_id="updateBooking",
)
def update_existing_booking(
    booking_id: int = Path(..., gt=0, description="Booking ID"),
    updated_data: BookingUpdate = ...,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token),
) -> BookingOut:
    updated = update_booking(db, booking_id, updated_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    return updated


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar reserva",
    response_model=None,
    responses={
        204: {"description": "Eliminado"},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Prohibido"},
        404: {"model": ErrorResponse, "description": "Reserva no encontrada"},
    },
    operation_id="deleteBooking",
)
def delete_existing_booking(
    booking_id: int = Path(..., gt=0, description="Booking ID"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token),
) -> None:
    deleted = delete_booking(db, booking_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/my/calendar",
    response_model=List[BookingOut],
    summary="Obtener reservas del host",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
    },
    operation_id="getMyBookingsCalendar",
)
def get_my_bookings_calendar(
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token),
) -> List[BookingOut]:
    return get_bookings_by_host(db, user_data["id"])


@router.get(
    "/my/earnings",
    response_model=EarningsReport,
    summary="Obtener reporte de ganancias",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
        422: {"description": "Error de validación"},
    },
    operation_id="getMyEarningsReport",
)
def get_my_earnings_report(
    start_date: date = Query(..., description="Fecha inicio"),
    end_date: date = Query(..., description="Fecha fin"),
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token),
) -> EarningsReport:
    total = get_earnings_by_host_and_dates(db, user_data["id"], start_date, end_date)
    return {"total_earnings": total or 0.0}


@router.get(
    "/report",
    summary="Obtener reservas agrupadas por periodo",
    responses={
        200: {"description": "OK"},
        400: {"model": ErrorResponse, "description": "Parámetros inválidos"},
        401: {"model": ErrorResponse},
    },
    operation_id="getBookingsReport",
)
def bookings_report(
    period: Literal["day", "week", "month"] = Query(..., description="Periodo: day, week, month"),
    accommodation_id: Optional[int] = Query(None, gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db),
):
    try:
        return get_bookings_grouped_by_period(db, period, accommodation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{booking_id}",
    response_model=BookingOut,
    summary="Obtener reserva por ID",
    responses={
        200: {"description": "OK"},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Reserva no encontrada"},
    },
    operation_id="getBookingById",
)
def retrieve_booking(
    booking_id: int = Path(..., gt=0, description="Booking ID"),
    db: Session = Depends(get_db),
) -> BookingOut:
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    return booking
