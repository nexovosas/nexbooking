# app/booking/services/image_service.py
from typing import Optional, List
import mimetypes
import uuid
from io import BytesIO

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError
from PIL import Image as PILImage

from app.booking.models.image_model import Image
from .s3_service import S3Service

# Reglas técnicas centralizadas
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def _normalize_mime(file: UploadFile) -> str:
    """
    Devuelve un MIME “seguro”:
    - Normaliza image/jpg -> image/jpeg
    - Si llega application/octet-stream o vacío, intenta deducir por extensión (.jpg/.png/.webp)
    """
    ct = (file.content_type or "").lower().strip()
    if ct == "image/jpg":
        ct = "image/jpeg"
    if ct and ct != "application/octet-stream":
        return ct

    guessed, _ = mimetypes.guess_type(file.filename or "")
    guessed = (guessed or "").lower().strip()
    if guessed == "image/jpg":
        guessed = "image/jpeg"

    return guessed or ct or "application/octet-stream"


def _enforce_file_rules(file: UploadFile):
    # 1) Tipo MIME (normalizado/fallback por extensión)
    ct = _normalize_mime(file)
    if ct not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {ct}. Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
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


def _process_image_to_webp(file: UploadFile, max_size=(1080, 1080)) -> UploadFile:
    """
    Procesa una imagen y la convierte a formato WebP optimizado
    antes de subirla a S3. Retorna un nuevo UploadFile compatible.
    """
    try:
        img = PILImage.open(file.file)

        # Transparencia y paleta
        if img.mode == "P":
            img = img.convert("RGBA")

        # Redimensionar manteniendo proporciones
        img.thumbnail(max_size, PILImage.Resampling.LANCZOS)

        # Guardar en buffer como WebP
        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=75, optimize=True)
        buffer.seek(0)

        # Generar un nuevo UploadFile-like con extensión .webp
        random_name = str(uuid.uuid4())[:16] + ".webp"
        optimized_file = UploadFile(
            filename=random_name,
            file=buffer,
            content_type="image/webp",
        )
        return optimized_file
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Image processing failed: {str(e)}"
        )


def create_image_for_accommodation_from_upload(
    file: UploadFile,
    accommodation_id: int,
    room_id: int,
    folder_name: str,
    db: Session,
) -> Image:
    _enforce_file_rules(file)

    s3 = S3Service()
    folder = f"{folder_name}/{(accommodation_id if room_id is None else room_id)}"
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
        room_id=room_id,
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def create_image_for_rooms_from_upload(
    file: UploadFile,
    rooms_id: int,
    db: Session,
    alt_text: Optional[str] = None,
) -> Image:
    _enforce_file_rules(file)

    s3 = S3Service()
    folder = f"rooms/{rooms_id}"
    try:
        obj = s3.upload_file(file, folder=folder)
    except ClientError as e:
        raise HTTPException(
            status_code=502, detail=f"S3 upload failed: {e.response.get('Error', {}).get('Message', 'unknown')}")

    db_image = Image(
        url=obj["key"],
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
    room_id: int,
    keys: List[str],
    alt_texts: Optional[List[Optional[str]]] = None,
) -> int:
    if not keys:
        return 0

    norm = [k.strip() for k in keys if k and k.strip()]
    seen = set()
    norm = [k for k in norm if not (k in seen or seen.add(k))]
    if not norm:
        return 0

    created = 0
    for idx, key in enumerate(norm):
        db_image = Image(
            url=key,
            alt_text=(alt_texts[idx] if alt_texts and idx <
                      len(alt_texts) else None),
            accommodation_id=accommodation_id,
            room_id=room_id,
        )
        db.add(db_image)
        created += 1

    db.commit()
    return created


def delete_images_by_ids(db: Session, image_ids: List[int], accommodation_id: int, room_id: int) -> int:
    if not image_ids:
        return 0

    imgs = (
        db.query(Image)
        .filter(Image.room_id == room_id if accommodation_id is None else Image.accommodation_id == accommodation_id, Image.id.in_(image_ids))
        .all()
    )
    if not imgs:
        return 0

    s3_keys = [img.url for img in imgs if img.url]
    s3 = S3Service()

    try:
        # ✅ Borrado en lote (hasta 1000 por request)
        s3.delete_objects(s3_keys)
    except ClientError as e:
        msg = e.response.get("Error", {}).get("Message", "unknown")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"S3 delete_objects failed: {msg}")

    for img in imgs:
        db.delete(img)
    db.commit()

    return len(imgs)
