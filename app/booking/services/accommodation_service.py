from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.booking.models.accommodation_model import Accommodation
from app.booking.models.room_model import Room
from app.booking.schemas.accommodation_schema import AccommodationCreate, AccommodationUpdate
from app.booking.services.image_service import create_image_for_accommodation

# 🔍 Buscar alojamientos con filtros
def search_accommodations_service(
    db: Session,
    name: Optional[str] = None,
    max_price: Optional[float] = None,
    services: Optional[str] = None
):
    query = db.query(Accommodation).join(Room)

    if max_price is not None:
        query = query.filter(Room.base_price <= max_price)
    if name:
        query = query.filter(Accommodation.name.ilike(f"%{name}%"))
    if services:
        service_list = [s.strip().lower() for s in services.split(",")]
        for s in service_list:
            query = query.filter(Accommodation.services.ilike(f"%{s}%"))

    query = query.group_by(Accommodation.id)
    return query.all()

# ➕ Crear alojamiento (host_id se inyecta desde el JWT)
def create_accommodation(db: Session, accommodation_data: AccommodationCreate, host_id: int):
    images_data = accommodation_data.images
    accommodation_dict = accommodation_data.model_dump(exclude={"images"})
    accommodation_dict["host_id"] = host_id  # <- dueño verdadero del JWT

    db_accommodation = Accommodation(**accommodation_dict)
    db.add(db_accommodation)
    db.commit()
    db.refresh(db_accommodation)

    if images_data:
        for img in images_data:
            create_image_for_accommodation(db, img, db_accommodation.id)

    return db_accommodation

# 📄 Obtener todos los alojamientos
def get_all_accommodations(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Accommodation).offset(skip).limit(limit).all()

# 📄 Obtener un alojamiento por ID
def get_accommodation(db: Session, accommodation_id: int):
    accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not accommodation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    return accommodation

# ✏️ Actualizar alojamiento (no permitir cambiar host_id)
def update_accommodation(db: Session, accommodation_id: int, updates: AccommodationUpdate):
    db_accommodation = get_accommodation(db, accommodation_id)
    for field, value in updates.model_dump(exclude_unset=True).items():
        if field == "host_id":
            continue  # blindaje extra, aunque ya no viene en el schema
        setattr(db_accommodation, field, value)
    db.commit()
    db.refresh(db_accommodation)
    return db_accommodation

# ❌ Eliminar alojamiento
def delete_accommodation(db: Session, accommodation_id: int):
    db_accommodation = get_accommodation(db, accommodation_id)
    db.delete(db_accommodation)
    db.commit()
    return db_accommodation

# 📄 Obtener alojamientos por host
def get_accommodations_by_host(db: Session, host_id: int):
    return db.query(Accommodation).filter(Accommodation.host_id == host_id).all()
