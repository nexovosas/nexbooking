from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.auth import verify_token
from app.db.session import get_db
from app.booking.schemas.booking_schema import *
from app.booking.services.booking_service import *
from datetime import date
from fastapi import Query

router = APIRouter( tags=["Bookings"])


# 🔹 Obtener ingresos totales por alojamiento
@router.get("/income")
def income_report(db: Session = Depends(get_db)):
    return get_income_by_accommodation(db)

# 🔹 Obtener todas las reservas
@router.get("/", response_model=List[BookingOut])
def list_bookings(db: Session = Depends(get_db)):
    return get_all_bookings(db)

# 🔹 Crear una nueva reserva
@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_new_booking(booking: BookingCreate, db: Session = Depends(get_db), user_data: dict = Depends(verify_token)):
    email = user_data.get("email")
    if not email:
        raise HTTPException(status_code=403, detail="Email no encontrado en token")
    
    return await create_booking(db, booking, user_email=email)  # ← usa await aquí

# 🔹 Actualizar una reserva
@router.put("/{booking_id}", response_model=BookingOut)
def update_existing_booking(
    booking_id: int, updated_data: BookingUpdate, db: Session = Depends(get_db),
     _: dict = Depends(verify_token)
):
    updated = update_booking(db, booking_id, updated_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Booking not found")
    return updated

# 🔹 Eliminar una reserva
@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_booking(booking_id: int, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    deleted = delete_booking(db, booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Booking not found")
    return

# 🔹 Obtener reservas del host para calendario
@router.get("/my/calendar", response_model=List[BookingOut])
def get_my_bookings_calendar(db: Session = Depends(get_db), user_data: dict = Depends(verify_token)):
    host_id = user_data["id"]
    return get_bookings_by_host(db, host_id)

# 🔹 Obtener reporte de ganancias del host
@router.get("/my/earnings", response_model=EarningsReport)
def get_my_earnings_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    host_id = user_data["id"]
    total = get_earnings_by_host_and_dates(db, host_id, start_date, end_date)
    return {"total_earnings": total or 0.0}

# 🔹 Obtener reservas agrupadas por periodo
@router.get("/report")
def bookings_report(
    period: str = Query(..., description="Options: day, week, month"),
    accommodation_id: int = None,
    db: Session = Depends(get_db)
):
    try:
        return get_bookings_grouped_by_period(db, period, accommodation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    




# 🔹 Obtener una reserva por ID
@router.get("/{booking_id}", response_model=BookingOut)
def retrieve_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking