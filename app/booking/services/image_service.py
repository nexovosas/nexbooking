# app/booking/services/image_service.py
from __future__ import annotations
from typing import Iterable, List, Optional, Mapping, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.booking.models.image_model import Image
from app.booking.schemas.image_schema import ImageCreate
from app.booking.services.s3_service import S3Service

def _normalize_image_item(item: Any) -> dict:
    """
    Acepta Pydantic (v2), dicts u objetos 'simples' y devuelve un dict con claves
    url, alt_text, is_main, filename, path (si existieran).
    """
    if hasattr(item, "model_dump"):  # Pydantic v2
        d = item.model_dump(exclude_unset=True, by_alias=True)
    elif isinstance(item, Mapping):
        d = dict(item)
    else:
        # fallback por atributos
        d = {
            "url": getattr(item, "url", None),
            "alt_text": getattr(item, "alt_text", None) or getattr(item, "alt", None),
            "is_main": getattr(item, "is_main", None),
            "filename": getattr(item, "filename", None),
            "path": getattr(item, "path", None),
        }
        return d

    # normaliza 'alt' -> 'alt_text'
    if "alt_text" not in d:
        d["alt_text"] = d.get("alt")

    return d

def create_image_for_accommodation_from_upload(
    file: UploadFile,
    accommodation_id: int,
    db: Session,
    alt_text: Optional[str] = None,
) -> Image:
    """
    Sube el archivo a S3/MinIO y crea el registro Image apuntando a la KEY.
    """
    s3 = S3Service()
    # carpeta: bookings/accommodations/<id>
    folder = f"accommodations/{accommodation_id}"
    obj = s3.upload_file(file, folder=folder)  # -> {"key": "...", "url": presigned_get, ...}

    db_image = Image(
        url=obj["key"],           # Guardamos la KEY (seguro para objetos privados)
        alt_text=alt_text or None,
        accommodation_id=accommodation_id,
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def create_images(
    db: Session,
    image_data: Iterable[Any],
    room_id: Optional[int] = None,
    accommodation_id: Optional[int] = None,
) -> List[Image]:
    if not room_id and not accommodation_id:
        raise ValueError("Either 'room_id' or 'accommodation_id' must be provided.")

    images: List[Image] = []
    for item in image_data or []:
        d = _normalize_image_item(item)
        new_image = Image(
            url=d.get("url"),
            alt_text=d.get("alt_text"),
            room_id=room_id,
            accommodation_id=accommodation_id,
        )
        db.add(new_image)
        images.append(new_image)

    db.commit()
    for image in images:
        db.refresh(image)
    return images
