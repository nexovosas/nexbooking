from __future__ import annotations
from datetime import date
import random
import string
from typing import List, Optional, Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.booking.models.availability_model import Availability, AvailabilityStatus
from app.booking.models.booking_model import Booking, BookingStatus
from app.booking.models.room_model import Room
from app.booking.models.accommodation_model import Accommodation
from app.booking.models.user_model import User
from app.booking.schemas.booking_schema import BookingCreate, BookingUpdate
from app.utils.email_utils import send_booking_confirmation_email


# Constants
VALID_PERIODS: tuple[str, ...] = ("day", "week", "month")


def get_income_by_accommodation(db: Session) -> List[tuple[str, float]]:
    """
    Return total income per accommodation, ordered by highest income.
    """
    stmt = (
        select(
            Accommodation.name.label("accommodation_name"),
            func.sum(Booking.total_price).label("total_income")
        )
        .join(Room, Booking.room_id == Room.id)
        .join(Accommodation, Room.accommodation_id == Accommodation.id)
        .group_by(Accommodation.id, Accommodation.name)
        .order_by(func.sum(Booking.total_price).desc())
    )
    return db.execute(stmt).all()


def get_bookings_grouped_by_period(
    db: Session,
    period: Literal["day", "week", "month"],
    accommodation_id: Optional[int] = None
) -> List[tuple[date, int]]:
    """
    Get bookings grouped by day, week, or month.
    Optionally filter by accommodation_id.
    """
    if period not in VALID_PERIODS:
        raise ValueError(f"Invalid period. Use: {VALID_PERIODS}")

    group_format = func.date_trunc(period, Booking.start_date)

    query = (
        db.query(
            group_format.label("period"),
            func.count(Booking.id).label("booking_count")
        )
        .join(Booking.room)
    )

    if accommodation_id:
        query = query.filter(Room.accommodation_id == accommodation_id)

    return query.group_by("period").order_by("period").all()


def generate_booking_code(db: Session) -> str:
    """
    Generate a unique booking code (RES-XXXXXX).
    """
    while True:
        code = f"RES-{''.join(random.choices(string.ascii_uppercase, k=2))}{''.join(random.choices(string.digits, k=4))}"
        if not db.query(Booking).filter_by(code=code).first():
            return code


async def create_booking(db: Session, booking_data: BookingCreate, user_email: str) -> dict:
    """
    Create a new booking, calculate total price if not provided,
    and send a confirmation email.
    """
    try:
        booking_dict = booking_data.model_dump(exclude={"email"})
        room = db.query(Room).filter(Room.id == booking_data.room_id).first()
        if not room:
            raise ValueError("Room not found")

        if 'total_price' not in booking_dict or booking_dict['total_price'] is None:
            nights = (booking_data.end_date - booking_data.start_date).days
            if nights <= 0:
                raise ValueError("Invalid booking dates")
            booking_dict['total_price'] = nights * room.base_price

        booking_dict.update({
            "status": BookingStatus.pending,
            "code": generate_booking_code(db)
        })

        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise ValueError("User not found")

        booking_dict['user_id'] = user.id

        new_booking = Booking(**booking_dict)
        db.add(new_booking)

        # Actualizamos el estado de la room
        room.is_available = False

        availabilities = (
            db.query(Availability)
            .filter(
                Availability.room_id == room.id,
                Availability.date >= booking_data.start_date,
                Availability.date < booking_data.end_date
            ).all()
        )
        
        for avail in availabilities:
            avail.status = AvailabilityStatus.not_available

        db.commit()
        db.refresh(new_booking)

        # booking_summary = (
        #     f"Booking Code: {new_booking.code}\n"
        #     f"Accommodation ID: {room.accommodation_id}\n"
        #     f"Room ID: {room.id}\n"
        #     f"Start Date: {new_booking.start_date}\n"
        #     f"End Date: {new_booking.end_date}\n"
        #     f"Total Price: ${new_booking.total_price:.2f}"
        # )

        # await send_booking_confirmation_email(to_email=user_email, booking_details=booking_summary)

        return {
            "message": "Booking created successfully. A confirmation email will be sent shortly.",
            "booking_id": new_booking.id
        }

    except Exception:
        db.rollback()
        raise


def get_all_bookings(db: Session) -> List[Booking]:
    bookings = db.query(Booking).all()
    result = []
    for b in bookings:
        result.append({
            "id": b.id,
            "code": b.code,
            "start_date": b.start_date,
            "end_date": b.end_date,
            "start_hour": b.start_hour,
            "end_hour": b.end_hour,
            "guests": b.guests,
            "status": b.status.value if hasattr(b.status, "value") else b.status,
            "total_price": b.total_price,
            "user_id": b.user_id,
            "room_id": b.room_id,
            "user_name": b.user.username if b.user else None,
            "room_name": b.room.room_name if b.room else None,
            "accommodation_id": b.room.accommodation_id if b.room else None
        })
    return result


def get_booking_by_id(db: Session, booking_id: int) -> Optional[Booking]:
    """Return a booking by ID."""
    return db.query(Booking).filter(Booking.id == booking_id).first()


def update_booking(db: Session, booking_id: int, updated_data: BookingUpdate) -> Optional[Booking]:
    """Update a booking by ID, adjusting room + availability if needed."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return None

    old_room_id = booking.room_id
    old_start = booking.start_date
    old_end = booking.end_date

    # Aplicar cambios al objeto booking
    for field, value in updated_data.model_dump(exclude_unset=True).items():
        setattr(booking, field, value)

    try:
        # Caso 1: Cambio de habitación o fechas
        if (
            booking.room_id != old_room_id
            or booking.start_date != old_start
            or booking.end_date != old_end
        ):
            #Liberar la habitación y disponibilidades anteriores
            old_room = db.query(Room).filter(Room.id == old_room_id).first()
            if old_room:
                old_room.is_available = True

            old_availabilities = (
                db.query(Availability)
                .filter(
                    Availability.room_id == old_room_id,
                    Availability.date >= old_start,
                    Availability.date < old_end,
                )
                .all()
            )
            for avail in old_availabilities:
                avail.status = AvailabilityStatus.available

            # 🔹 Ocupar la nueva habitación y disponibilidades
            new_room = db.query(Room).filter(
                Room.id == booking.room_id).first()
            if new_room:
                new_room.is_available = False

            new_availabilities = (
                db.query(Availability)
                .filter(
                    Availability.room_id == booking.room_id,
                    Availability.date >= booking.start_date,
                    Availability.date < booking.end_date,
                )
                .all()
            )
            for avail in new_availabilities:
                avail.status = AvailabilityStatus.not_available

        db.commit()
        db.refresh(booking)
        return booking

    except SQLAlchemyError:
        db.rollback()
        raise


def delete_booking(db: Session, booking_id: int) -> bool:
    """Delete a booking by ID."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return False

    try:
        db.delete(booking)
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise


def get_bookings_by_host(db: Session, host_id: int) -> List[Booking]:
    """Get all bookings for a specific host."""
    return (
        db.query(Booking)
        .join(Room)
        .join(Accommodation)
        .filter(Accommodation.host_id == host_id)
        .all()
    )


def get_earnings_by_host_and_dates(
    db: Session,
    host_id: int,
    start_date: date,
    end_date: date
) -> Optional[float]:
    """Get total earnings for a host within a date range."""
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
