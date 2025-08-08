from sqlalchemy.orm import Session
from app.booking.models.availability_model import Availability
from app.booking.schemas.availability_schema import (
    AvailabilityCreate, AvailabilityUpdate
)
from typing import List, Optional


def create_availability(db: Session, availability_data: AvailabilityCreate) -> Availability:
    new_availability = Availability(**availability_data.dict())
    db.add(new_availability)
    db.commit()
    db.refresh(new_availability)
    return new_availability


def get_availabilities_by_room(db: Session, room_id: int) -> List[Availability]:
    return db.query(Availability).filter(Availability.room_id == room_id).all()


def get_availability_by_id(db: Session, availability_id: int) -> Optional[Availability]:
    return db.query(Availability).filter(Availability.id == availability_id).first()


def update_availability(db: Session, availability_id: int, availability_data: AvailabilityUpdate) -> Optional[Availability]:
    availability = db.query(Availability).filter(Availability.id == availability_id).first()
    if not availability:
        return None

    for field, value in availability_data.dict(exclude_unset=True).items():
        setattr(availability, field, value)

    db.commit()
    db.refresh(availability)
    return availability


def delete_availability(db: Session, availability_id: int) -> bool:
    availability = db.query(Availability).filter(Availability.id == availability_id).first()
    if not availability:
        return False

    db.delete(availability)
    db.commit()
    return True
