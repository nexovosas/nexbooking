from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.auth import verify_token
from app.db.session import get_db

from app.booking.schemas.accommodation_schema import *
from app.booking.services.accommodation_service import *

router = APIRouter(tags=["Accommodations"])


@router.post("/", response_model=AccommodationOut)
def create_accommodation(accommodation_data: AccommodationCreate, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    return create_accommodation(db=db, accommodation_data=accommodation_data)


@router.get("/", response_model=List[AccommodationOut])
def read_all_accommodation(db: Session = Depends(get_db)):
    return get_all_accommodations(db)


@router.put("/{accommodation_id}", response_model=AccommodationOut)
def update(accommodation_id: int, hospedaje: AccommodationUpdate, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    updated = update_accommodation(db, accommodation_id, hospedaje)
    if not updated:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return updated

@router.delete("/{accommodation_id}")
def delete_accommodation(accommodation_id: int, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    success = delete_accommodation(db, accommodation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return {"detail": "Accommodation deleted successfully"}

@router.get("/my", response_model=List[AccommodationOut])
def get_my_accommodations(db: Session = Depends(get_db), user_data: dict = Depends(verify_token)):
    host_id = user_data["id"]
    return get_accommodations_by_host(db, host_id)

# 🔍 Buscar alojamientos con filtros
@router.get("/search", response_model=List[AccommodationOut])
def search_accommodations(
    name: str = "", 
    max_price: float = 99999.0, 
    services: str = "",  # cadena separada por comas
    db: Session = Depends(get_db)
):
    return search_accommodations_service(db, name, max_price, services)



@router.get("/{accommodation_id}", response_model=AccommodationOut)
def read_one_accommodation(accommodation_id: int, db: Session = Depends(get_db)):
    db_accommodation = get_accommodation(db, accommodation_id)
    if not db_accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return db_accommodation