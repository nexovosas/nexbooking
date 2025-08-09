# app/booking/services/availability_service.py
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.booking.models.availability_model import Availability
from app.booking.schemas.availability_schema import AvailabilityCreate, AvailabilityUpdate


def create_availability(db: Session, availability_data: AvailabilityCreate) -> Availability:
    """
    Create a new availability entry for a room.
    """
    new_availability = Availability(**availability_data.model_dump())
    db.add(new_availability)
    db.commit()
    db.refresh(new_availability)
    return new_availability


def get_availabilities_by_room(db: Session, room_id: int) -> List[Availability]:
    """
    Retrieve all availabilities for a given room ID.
    """
    return db.query(Availability).filter(Availability.room_id == room_id).all()


def get_availability_by_id(db: Session, availability_id: int) -> Optional[Availability]:
    """
    Retrieve a single availability entry by its ID.
    """
    return db.query(Availability).filter(Availability.id == availability_id).first()


def update_availability(
    db: Session, availability_id: int, availability_data: AvailabilityUpdate
) -> Optional[Availability]:
    """
    Update an availability entry if it exists.
    """
    availability = db.query(Availability).filter(Availability.id == availability_id).first()
    if not availability:
        return None

    for field, value in availability_data.model_dump(exclude_unset=True).items():
        setattr(availability, field, value)

    db.commit()
    db.refresh(availability)
    return availability


def delete_availability(db: Session, availability_id: int) -> bool:
    """
    Delete an availability entry by its ID.
    """
    availability = db.query(Availability).filter(Availability.id == availability_id).first()
    if not availability:
        return False

    db.delete(availability)
    db.commit()
    return True
