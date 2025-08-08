from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.booking.models.booking_model import Booking
from app.booking.models.room_model import Room
from app.booking.models.accommodation_model import Accommodation
from app.booking.models.user_model import *
from app.booking.schemas.booking_schema import *
import random
import string
from sqlalchemy import func,select
from datetime import datetime
from app.utils.email_utils import send_booking_confirmation_email  


def get_income_by_accommodation(db: Session):

    stmt = select(
        Accommodation.name.label("accommodation_name"),
        func.sum(Booking.total_price).label("total_income")
    )
    stmt = stmt.join(
        Room,
        Booking.room_id == Room.id
    ).join(
        Accommodation,
        Room.accommodation_id == Accommodation.id
    )
    stmt = stmt.group_by(
        Accommodation.id, Accommodation.name
    )
    stmt = stmt.order_by(
        func.sum(Booking.total_price).desc()
    )
    return db.execute(stmt).all()

# 🔹 Obtener reservas agrupadas por día, semana o mes
def get_bookings_grouped_by_period(db: Session, period: str, accommodation_id: int = None):
    if period not in ['day', 'week', 'month']:
        raise ValueError("Invalid period. Use: 'day', 'week', or 'month'")

    if period == 'day':
        group_format = func.date_trunc('day', Booking.start_date)
    elif period == 'week':
        group_format = func.date_trunc('week', Booking.start_date)
    else:  # month
        group_format = func.date_trunc('month', Booking.start_date)

    query = db.query(
        group_format.label("period"),
        func.count(Booking.id).label("booking_count")
    ).join(Booking.room)  # join con Room para acceder a Room.accommodation_id

    if accommodation_id:
        query = query.filter(Room.accommodation_id == accommodation_id)

    query = query.group_by("period").order_by("period")

    return query.all()



# 🔹 Generar un código de reserva único
def generate_booking_code() -> str:
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=4))
    return f"RES-{letters}{numbers}"


# 🔹 Crear una nueva reserva con cálculo automático de total_price
async def create_booking(db: Session, booking_data: BookingCreate, user_email: str):
    try:
        # Generar y validar código único
        code = generate_booking_code()
        while db.query(Booking).filter_by(code=code).first():
            code = generate_booking_code()

        booking_dict = booking_data.dict()

        # Verificar que la habitación exista
        room = db.query(Room).filter(Room.id == booking_data.room_id).first()
        if not room:
            raise ValueError("Room not found")

        # Calcular total_price si no está presente
        if 'total_price' not in booking_dict or booking_dict['total_price'] is None:
            nights = (booking_data.end_date - booking_data.start_date).days
            if nights <= 0:
                raise ValueError("Invalid booking dates")
            booking_dict['total_price'] = nights * room.base_price

        # Establecer estado de confirmación como 'pending'
        booking_dict['status'] = BookingStatus.pending
        booking_dict['code'] = code

        # Obtener el usuario según su email
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise ValueError("User not found")

        booking_dict['user_id'] = user.id

        # Crear la reserva
        new_booking = Booking(**booking_dict)
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        # Enviar correo de confirmación
        booking_summary = (
            f"Booking Code: {new_booking.code}\n"
            f"Accommodation ID: {room.accommodation_id}\n"
            f"Room ID: {room.id}\n"
            f"Start Date: {new_booking.start_date}\n"
            f"End Date: {new_booking.end_date}\n"
            f"Total Price: ${new_booking.total_price:.2f}"
        )

        await send_booking_confirmation_email(to_email=user_email, booking_details=booking_summary)

        return {
            "message": "Booking created successfully. A confirmation email will be sent shortly.",
            "booking": new_booking
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise e

# 🔹 Obtener todas las reservas
def get_all_bookings(db: Session):
    return db.query(Booking).all()


# 🔹 Obtener una reserva por ID
def get_booking_by_id(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()


# 🔹 Actualizar una reserva existente
def update_booking(db: Session, booking_id: int, updated_data: BookingUpdate):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return None

    for field, value in updated_data.dict(exclude_unset=True).items():
        setattr(booking, field, value)

    try:
        db.commit()
        db.refresh(booking)
        return booking
    except SQLAlchemyError as e:
        db.rollback()
        raise e


# 🔹 Eliminar una reserva
def delete_booking(db: Session, booking_id: int):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return None

    try:
        db.delete(booking)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise e
# 🔹 Obtener reservas por el ID del host ver cañemdarops de reservas 
def get_bookings_by_host(db: Session, host_id: int):
    return (
        db.query(Booking)
        .join(Room)
        .join(Accommodation)
        .filter(Accommodation.host_id == host_id)
        .all()
    )


# 🔹 Obtener ganancias del host por fechas
def get_earnings_by_host_and_dates(db: Session, host_id: int, start_date: date, end_date: date):
    return (
        db.query(func.sum(Booking.total_price).label("total_earnings"))
        .join(Room)
        .join(Accommodation)
        .filter(
            Accommodation.host_id == host_id,
            Booking.status == BookingStatus.confirmed,
            Booking.start_date >= start_date,
            Booking.end_date <= end_date
        )
        .scalar()
    )
