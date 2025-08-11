# app/booking/services/accommodation_service.py
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from fastapi import HTTPException, status

from app.booking.models.accommodation_model import Accommodation
from app.booking.models.room_model import Room
from app.booking.schemas.accommodation_schema import AccommodationCreate, AccommodationUpdate
from app.booking.services.image_service import create_image_for_accommodation

def _host_exists(db: Session, host_id: int) -> bool:
    # Chequeo directo contra la tabla "user" de Django
    row = db.execute(text('SELECT 1 FROM "user" WHERE id = :id LIMIT 1'), {"id": host_id}).first()
    return bool(row)

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
        for s in [x.strip().lower() for x in services.split(",")]:
            query = query.filter(Accommodation.services.ilike(f"%{s}%"))
    return query.group_by(Accommodation.id).all()

def create_accommodation(db: Session, accommodation_data: AccommodationCreate, host_id: int):
    # 1) Verificar host
    if not _host_exists(db, host_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found for provided token id.")

    # 2) Evitar duplicados (por UNIQUE host_id + name + location)
    exists = (
        db.query(Accommodation)
        .filter(
            Accommodation.host_id == host_id,
            Accommodation.name == accommodation_data.name,
            Accommodation.location == accommodation_data.location,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Accommodation already exists for this host and location.")

    # 3) Crear registro
    images_data = accommodation_data.images
    payload = accommodation_data.model_dump(exclude={"images"})
    payload["host_id"] = host_id

    acc = Accommodation(**payload)
    db.add(acc)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "foreign key" in msg or "fk" in msg:
            raise HTTPException(status_code=404, detail="Host not found (foreign key).")
        if "unique" in msg:
            raise HTTPException(status_code=409, detail="Unique constraint violated (host, name, location).")
        raise HTTPException(status_code=409, detail="Integrity error.")

    db.refresh(acc)

    # 4) Imágenes (si aplica)
    if images_data:
        for img in images_data:
            create_image_for_accommodation(db, img, acc.id)

    return acc

def get_all_accommodations(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Accommodation).offset(skip).limit(limit).all()

def get_accommodation(db: Session, accommodation_id: int):
    acc = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    return acc

def update_accommodation(db: Session, accommodation_id: int, updates: AccommodationUpdate):
    acc = get_accommodation(db, accommodation_id)
    for field, value in updates.model_dump(exclude_unset=True).items():
        if field == "host_id":
            continue
        setattr(acc, field, value)
    db.commit()
    db.refresh(acc)
    return acc

def delete_accommodation(db: Session, accommodation_id: int):
    acc = get_accommodation(db, accommodation_id)
    db.delete(acc)
    db.commit()
    return acc

def get_accommodations_by_host(db: Session, host_id: int):
    return db.query(Accommodation).filter(Accommodation.host_id == host_id).all()
