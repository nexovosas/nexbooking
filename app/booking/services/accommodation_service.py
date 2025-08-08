from sqlalchemy.orm import Session
from app.booking.models.accommodation_model import Accommodation
from app.booking.schemas.accommodation_schema import *
from app.booking.services.image_service import create_image_for_accommodation
from sqlalchemy import and_
from app.booking.models.booking_model import Booking
from app.booking.models.room_model import Room
from app.booking.models.accommodation_model import Accommodation

# 🔍 Buscar alojamientos con filtros
def search_accommodations_service(db: Session, name: str, max_price: float, services: str):
    query = (
        db.query(Accommodation)
        .join(Room)  # JOIN directo con Room
        .filter(Room.base_price <= max_price)  # Filtro de precio
        .group_by(Accommodation.id)  # Necesario para evitar duplicados
    )

    if name:
        query = query.filter(Accommodation.name.ilike(f"%{name}%"))

    if services:
        service_list = [s.strip().lower() for s in services.split(",")]
        for s in service_list:
            query = query.filter(Accommodation.services.ilike(f"%{s}%"))

    return query.all()



# Create accommodation
def create_accommodation(db: Session, accommodation_data: AccommodationCreate):
    # Separa los datos de imagen
    images_data = accommodation_data.images
    accommodation_dict = accommodation_data.dict(exclude={"images"})

    db_accommodation = Accommodation(**accommodation_dict)
    db.add(db_accommodation)
    db.commit()
    db.refresh(db_accommodation)

    # Crear imágenes si las hay
    if images_data:
        for img in images_data:
            create_image_for_accommodation(db, img, db_accommodation.id)

    return db_accommodation

# Get all accommodations
def get_all_accommodations(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Accommodation).offset(skip).limit(limit).all()

# Get one
def get_accommodation(db: Session, accommodation_id: int):
    return db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()


# Update accommodation
def update_accommodation(db: Session, accommodation_id: int, updates: AccommodationUpdate):
    db_accommodation = get_accommodation(db, accommodation_id)
    if not db_accommodation:
        return None
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(db_accommodation, field, value)
    db.commit()
    db.refresh(db_accommodation)
    return db_accommodation

# Delete accommodation
def delete_accommodation(db: Session, accommodation_id: int):
    db_accommodation = get_accommodation(db, accommodation_id)
    if db_accommodation:
        db.delete(db_accommodation)
        db.commit()
    return db_accommodation

def get_accommodations_by_host(db: Session, host_id: int):
    return db.query(Accommodation).filter(Accommodation.host_id == host_id).all()


