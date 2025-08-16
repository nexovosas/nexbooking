# app/booking/services/accommodation_service.py
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from fastapi import HTTPException, status

from app.booking.models.accommodation_model import Accommodation
from app.booking.models.room_model import Room
from app.booking.schemas.accommodation_schema import AccommodationCreate, AccommodationUpdate
from app.booking.services.s3_service import S3Service

def _host_exists(db: Session, host_id: int) -> bool:
    # Chequeo directo contra la tabla "user" de Django
    row = db.execute(text('SELECT 1 FROM "user" WHERE id = :id LIMIT 1'), {"id": host_id}).first()
    return bool(row)

def search_accommodations_service(
    db: Session,
    name: Optional[str] = None,
    location: Optional[str] = None,
    max_price: Optional[float] = None,
    services: Optional[str] = None,
):
    # Normalizar entradas
    name = (name or "").strip() or None
    services = (services or "").strip() or None
    location = (location or "").strip() or None
    # OUTER JOIN para no perder alojamientos sin rooms
    query = (
        db.query(Accommodation)
        .outerjoin(Room, Room.accommodation_id == Accommodation.id)
    )
    if max_price is not None:
        query = query.filter(Room.base_price <= max_price)
    if name:
        query = query.filter(Accommodation.name.ilike(f"%{name}%"))
    if location:
        query = query.filter(Accommodation.location.ilike(f"%{location}%"))
    if services:
        # Cambia a OR si prefieres que coincida con cualquiera de los términos
        terms = [t.strip().lower() for t in services.split(",") if t.strip()]
        # AND (todos los términos):
        for t in terms:
            query = query.filter(Accommodation.services.ilike(f"%{t}%"))
        # ---- OR (descomenta esto y comenta el bucle de arriba si prefieres OR) ----
        # from sqlalchemy import or_
        # ors = [Accommodation.services.ilike(f"%{t}%") for t in terms]
        # query = query.filter(or_(*ors))
    return query.distinct(Accommodation.id).all()

def create_accommodation(
    db: Session,
    accommodation_data: AccommodationCreate,
    host_id: int,
) -> Accommodation:
    # 1) Verificar host
    if not _host_exists(db, host_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found for provided token id.")

    # 2) Evitar duplicados (UNIQUE host_id + name)
    exists = (
        db.query(Accommodation)
        .filter(
            Accommodation.host_id == host_id,
            Accommodation.name == accommodation_data.name,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Accommodation already exists for this host and location.",
        )

    # 3) Convertir Pydantic -> dict y limpiar campos no persistentes
    payload = accommodation_data.model_dump(exclude_unset=True, exclude_none=True)
    payload.pop("images", None)   # si tu schema aún lo trae
    payload.pop("host_id", None)  # el host viene del token, no del payload

    # 4) Crear registro
    acc = Accommodation(**payload, host_id=host_id)
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
    return acc

def get_all_accommodations(db: Session, skip: int = 0, limit: int = 10):
    return (
        db.query(Accommodation)
        .options(
            selectinload(Accommodation.images),
            selectinload(Accommodation.rooms),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_accommodation(db: Session, accommodation_id: int):
    acc = (
        db.query(Accommodation)
        .options(
            selectinload(Accommodation.images),
            selectinload(Accommodation.rooms),
        )
        .filter(Accommodation.id == accommodation_id)
        .first()
    )
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
    acc = get_accommodation(db, accommodation_id)  # 404 si no existe

    # borra objetos S3 bajo el prefijo del alojamiento
    s3 = S3Service()
    s3.delete_objects(f"accommodations/{accommodation_id}")

    db.delete(acc)
    db.commit()
    return acc

def get_accommodations_by_host(db: Session, host_id: int):
    return db.query(Accommodation).filter(Accommodation.host_id == host_id).all()
