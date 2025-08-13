# app/booking/services/image_service.py
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError

from app.booking.models.image_model import Image
from .s3_service import S3Service

# Reglas técnicas centralizadas
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB

def _enforce_file_rules(file: UploadFile):
    # 1) Tipo MIME
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )
    # 2) Tamaño por streaming (sin cargar todo a RAM)
    CHUNK = 1024 * 1024
    total = 0
    pos = file.file.tell()
    try:
        while True:
            chunk = file.file.read(CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Max {MAX_IMAGE_BYTES // (1024*1024)} MB",
                )
    finally:
        file.file.seek(pos)

def create_image_for_accommodation_from_upload(
    file: UploadFile,
    accommodation_id: int,
    db: Session,
) -> Image:
    _enforce_file_rules(file)

    s3 = S3Service()
    folder = f"accommodations/{accommodation_id}"
    try:
        obj = s3.upload_file(file, folder=folder)  # {"key": "..."}
    except ClientError as e:
        raise HTTPException(
            status_code=502,
            detail=f"S3 upload failed: {e.response.get('Error', {}).get('Message', 'unknown')}"
        )

    db_image = Image(
        url=obj["key"],                 # guardamos la KEY (no URL) en BD
        alt_text=file.filename or None,
        accommodation_id=accommodation_id,
    )
    db.add(db_image)
    db.commit()                        # ⬅️ importante
    db.refresh(db_image)               # ⬅️ para que tenga id, etc.
    return db_image


def create_image_for_rooms_from_upload(
    file: UploadFile,
    rooms_id: int,
    db: Session,
    alt_text: Optional[str] = None,
) -> Image:
    """
    Sube el archivo a S3/MinIO y crea el registro Image apuntando a la KEY.
    """
    _enforce_file_rules(file)

    s3 = S3Service()
    folder = f"rooms/{rooms_id}"
    try:
        obj = s3.upload_file(file, folder=folder)  # {"key": "...", "url": presigned_get, ...}
    except ClientError as e:
        raise HTTPException(status_code=502, detail=f"S3 upload failed: {e.response.get('Error', {}).get('Message', 'unknown')}")

    db_image = Image(
        url=obj["key"],           # Guardamos la KEY (seguro para privados)
        alt_text=alt_text or None,
        rooms_id=rooms_id,
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def create_images_for_accommodation_from_keys(
    db: Session,
    accommodation_id: int,
    keys: List[str],
    alt_texts: Optional[List[Optional[str]]] = None,
) -> int:
    """
    Registra en DB imágenes que YA fueron subidas a S3 mediante presigned PUT.
    Guarda la KEY en `url` (recomendado para buckets privados).
    """
    if not keys:
        return 0

    # Normaliza y deduplica
    norm = [k.strip() for k in keys if k and k.strip()]
    seen = set()
    norm = [k for k in norm if not (k in seen or seen.add(k))]
    if not norm:
        return 0

    created = 0
    for idx, key in enumerate(norm):
        db_image = Image(
            url=key,
            alt_text=(alt_texts[idx] if alt_texts and idx < len(alt_texts) else None),
            accommodation_id=accommodation_id,
        )
        db.add(db_image)
        created += 1

    db.commit()
    return created

def delete_images_by_ids(
    db: Session,
    image_ids: List[int],
    accommodation_id: int,
) -> int:
    """
    Elimina imágenes por IDs pertenecientes al accommodation dado.
    - Borra en batch en S3 con S3Service.delete_objects(...)
    - Elimina filas de DB en la misma transacción.
    """
    if not image_ids:
        return 0

    imgs = (
        db.query(Image)
        .filter(Image.accommodation_id == accommodation_id, Image.id.in_(image_ids))
        .all()
    )
    if not imgs:
        return 0

    s3_keys = [img.url for img in imgs if img.url]
    s3 = S3Service()

    # 1) Borrado en S3 (batch)
    try:
        s3.delete_objects(s3_keys)
    except ClientError as e:
        # Transporta un error 502 con detalle del proveedor
        msg = e.response.get("Error", {}).get("Message", "unknown")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 delete_objects failed: {msg}",
        )

    # 2) Borrado en DB
    for img in imgs:
        db.delete(img)
    db.commit()

    return len(imgs)