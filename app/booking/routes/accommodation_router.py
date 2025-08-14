from __future__ import annotations

# Stdlib
import json
from json import JSONDecodeError
from typing import List, Optional, Union, Iterable

# FastAPI / SQLAlchemy
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

# Proyecto
from app.auth.verify_token import verify_token
from app.common.schemas import ErrorResponse
from app.db.session import get_db
import logging

log = logging.getLogger("uvicorn.error")

from app.booking.schemas.accommodation_schema import (
    AccommodationCreate,
    AccommodationOut,
    AccommodationUpdate,
)
from app.booking.services.accommodation_service import (
    create_accommodation,
    get_all_accommodations,
    update_accommodation,
    delete_accommodation,
    get_accommodations_by_host,
    search_accommodations_service,
    get_accommodation,
)
from app.booking.services.image_service import (
    create_image_for_accommodation_from_upload,
    create_images_for_accommodation_from_keys,
    delete_images_by_ids,
)
from app.booking.services.s3_service import S3Service


router = APIRouter(tags=["Accommodations"], prefix="/accommodations")

# =========================
#  Config de negocio
# =========================
MAX_IMAGES_PER_ACC = 10         # Máximo total por alojamiento
MAX_FILES_CREATE = 10           # Máximo archivos aceptados al crear


# =========================
#  Helpers
# =========================
def _ensure_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _parse_delete_ids(raw: Union[None, str, List[int], List[str]]) -> List[int]:
    """
    Acepta:
      - lista de enteros [1,2]
      - lista de strings ['1','2']
      - string CSV "1,2,3"
      - JSON string "[1,2,3]"
      - string de un solo valor "14"
    Devuelve siempre List[int].
    """
    if raw is None:
        return []
    if isinstance(raw, list):
        return [int(x) for x in raw]
    s = str(raw).strip()
    if not s:
        return []
    try:
        j = json.loads(s)
        if isinstance(j, list):
            return [int(x) for x in j]
    except Exception:
        pass
    return [int(x) for x in s.split(",") if x.strip()]


def _to_str_list(raw: Union[None, str, List[str]]) -> List[str]:
    """
    Normaliza a lista de strings, limpiando espacios y vacíos.
    """
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    s = str(raw).strip()
    return [s] if s else []


def _attach_presigned_urls(acc):
    """
    Reemplaza en memoria (solo para respuesta) las keys S3 por presigned GET URLs.
    """
    if acc is None:
        return acc
    s3 = S3Service()

    def _sign(img):
        u = getattr(img, "url", None)
        if isinstance(u, str) and not u.lower().startswith(("http://", "https://")):
            img.url = s3.presign_get_url(u)

    if isinstance(acc, list):
        for a in acc:
            for img in getattr(a, "images", []) or []:
                _sign(img)
        return acc

    for img in getattr(acc, "images", []) or []:
        _sign(img)
    return acc


def _validate_images_count(images: Optional[List[UploadFile]]):
    if not images:
        return
    if len(images) > MAX_FILES_CREATE:
        raise HTTPException(status_code=422, detail=f"Max {MAX_FILES_CREATE} images allowed")

def _uploads_to_list(new_images) -> List[UploadFile]:
    if new_images is None:
        return []
    if isinstance(new_images, UploadFile):
        return [new_images]
    if isinstance(new_images, list):
        return [f for f in new_images if isinstance(f, UploadFile)]
    return []

# =========================
#  Endpoints
# =========================

# ------- CREATE -------
@router.post(
    "/",
    response_model=AccommodationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new accommodation",
    description="Creates a new accommodation and optionally its images. Requires authentication.",
    operation_id="createAccommodation",
    responses={
        201: {"description": "Created"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden (not owner)"},
        409: {"model": ErrorResponse, "description": "Conflict (duplicate)"},
    },
)
def create_accommodation_endpoint(
    payload: str = Form(..., description="AccommodationCreate en JSON (string)"),
    images: List[UploadFile] = File(..., description="Images for the accommodation"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    """
    Crea el alojamiento y sube imágenes. `payload` debe ser un JSON string válido (Pydantic v2).
    """
    acc_in = AccommodationCreate.model_validate_json(payload)
    _validate_images_count(images)

    acc = create_accommodation(db, acc_in, host_id=user["id"])

    # Subir imágenes (si llegan)
    for f in images or []:
        try:
            f.file.seek(0)  # robustez por si algún middleware leyó el stream
        except Exception:
            pass
        create_image_for_accommodation_from_upload(f, acc.id, db)

    # (Opcional) Firmar URLs para respuesta
    _attach_presigned_urls(acc)
    return acc


# ------- PRESIGN -------
@router.post(
    "/{accommodation_id}/images/presign",
    summary="Get presigned PUT URLs for direct S3 upload",
    description="Devuelve URLs presignadas para subir imágenes directo a S3/MinIO.",
    operation_id="presignAccommodationImages",
    responses={200: {"description": "OK"}},
)
def presign_accommodation_images(
    accommodation_id: int = Path(..., gt=0),
    count: int = Form(1, ge=1, le=MAX_IMAGES_PER_ACC),
    content_type: str = Form("image/jpeg"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    acc = get_accommodation(db, accommodation_id)
    if acc.host_id != user.get("id"):
        raise HTTPException(status_code=403, detail="Forbidden")

    if len(acc.images or []) + count > MAX_IMAGES_PER_ACC:
        raise HTTPException(status_code=422, detail=f"Max {MAX_IMAGES_PER_ACC} images per accommodation")

    s3 = S3Service()
    return s3.presign_put_urls(count=count, folder=f"accommodations/{accommodation_id}", content_type=content_type)


# ------- LIST / MY / SEARCH / GET -------
@router.get("/", response_model=List[AccommodationOut], operation_id="listAccommodations")
def read_all_accommodations(db: Session = Depends(get_db)):
    accs = get_all_accommodations(db)
    _attach_presigned_urls(accs)
    return accs


@router.get("/my", response_model=List[AccommodationOut], operation_id="listMyAccommodations")
def get_my_accommodations(db: Session = Depends(get_db), user: dict = Depends(verify_token)):
    host_id = user.get("id")
    if host_id is None:
        raise HTTPException(status_code=401, detail="Invalid token: user id missing")
    accs = get_accommodations_by_host(db, host_id)
    _attach_presigned_urls(accs)
    return accs


@router.get("/search", response_model=List[AccommodationOut], operation_id="searchAccommodations")
def search_accommodations(
    name: Optional[str] = None,
    location: Optional[str] = None,
    max_price: Optional[float] = None,
    services: Optional[str] = None,
    db: Session = Depends(get_db),
):
    accs = search_accommodations_service(db, name, location, max_price, services)
    _attach_presigned_urls(accs)
    return accs


@router.get(
    "/{accommodation_id}",
    response_model=AccommodationOut,
    summary="Retrieve an accommodation by ID",
    responses={200: {"description": "OK"}, 404: {"model": ErrorResponse}},
    operation_id="getAccommodationById",
)
def read_one_accommodation(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db),
):
    acc = get_accommodation(db, accommodation_id)
    _attach_presigned_urls(acc)
    return acc


# ------- UPDATE (Multipart) -------
@router.put(
    "/{accommodation_id}",
    response_model=AccommodationOut,
    summary="Update accommodation (multipart): add/remove images and optional fields",
    description=(
        "Multipart para agregar/quitar imágenes y actualizar campos.\n"
        "- `updates_json`: JSON string matching AccommodationUpdate (opcional)\n"
        "- `new_image`: un archivo (opcional)\n"
        "- `new_images`: varios archivos (opcional, usa 'Add item')\n"
        "- `delete_image_ids`: IDs a borrar (array o '1,2,3' o '[1,2,3]')\n"
        "- `new_image_keys`: keys S3 ya subidas (array o string)\n"
    ),
    operation_id="updateAccommodationMultipart",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "updates_json": {
                                "type": "string",
                                "description": "JSON string de AccommodationUpdate",
                                "example": (
                                    "{\"name\":\"La Montera 5\",\"description\":\"Updated description\","
                                    "\"services\":\"glamping,spa\",\"is_active\":false,\"type\":\"Glamping\","
                                    "\"pet_friendly\":true,\"location\":\"Updated Location\"}"
                                ),
                            },
                            "new_images": {  # <-- multiple files
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Sube VARIAS imágenes (usa 'Add item')."
                            },
                            "delete_image_ids": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "IDs de imágenes a eliminar."
                            },
                            "new_image_keys": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "S3 keys ya subidas por presigned PUT."
                            },
                        },
                        "required": []
                    },
                    "encoding": {
                        # ¡NO forzar updates_json a application/json!
                        "new_image": {"style": "form", "explode": True},
                        "new_images": {"style": "form", "explode": True},
                        "delete_image_ids": {"style": "form", "explode": True},
                        "new_image_keys": {"style": "form", "explode": True},
                    },
                }
            }
        }
    },
)
async def update_accommodation_endpoint(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),

    # TEXTO (no blob)
    updates_json: Optional[str] = Form(None, description="AccommodationUpdate como JSON string"),

    # ARCHIVOS: ofrecemos single y multiple para que /docs sea cómodo
    new_images: List[UploadFile] = File(None, description="Sube VARIAS imágenes (usa 'Add item')"),

    # FLEXIBLES (aceptan array o string)
    delete_image_ids: Optional[Union[List[int], str]] = Form(None, description="IDs de imágenes a eliminar"),
    new_image_keys: Optional[Union[List[str], str]] = Form(None, description="S3 keys ya subidas por presigned"),

    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    # 0) Auth & ownership
    acc = get_accommodation(db, accommodation_id)
    if acc.host_id != user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # 1) Actualizar campos
    if updates_json:
        try:
            payload = json.loads(updates_json)
        except JSONDecodeError as e:
            raise HTTPException(
                status_code=422,
                detail=f"updates_json is not valid JSON (line {e.lineno}, col {e.colno}): {e.msg}",
            )
        updates = AccommodationUpdate.model_validate(payload)
        acc = update_accommodation(db, accommodation_id, updates)

    # 2) Normalizaciones
    #files_to_add: List[UploadFile] = []
    #if new_images:
    #   files_to_add.extend([f for f in new_images if isinstance(f, UploadFile) and getattr(f, "filename", "")])

    ids_to_delete = _parse_delete_ids(delete_image_ids)
    keys_to_add = list(dict.fromkeys(_to_str_list(new_image_keys)))  # dedupe

    # 3) Cupo
    existing = len(acc.images or [])
    final_count = existing - len(ids_to_delete) + (0 if new_images is None else len(new_images)) + len(keys_to_add)
    if final_count > MAX_IMAGES_PER_ACC:
        raise HTTPException(status_code=422, detail=f"Max {MAX_IMAGES_PER_ACC} images per accommodation")

    # 4) Aplicar cambios
    if ids_to_delete:
        delete_images_by_ids(db, ids_to_delete, accommodation_id)

    for f in new_images or []:
        try:
            f.file.seek(0)
        except Exception:
            pass
        create_image_for_accommodation_from_upload(f, accommodation_id, db)

    if keys_to_add:
        create_images_for_accommodation_from_keys(db, accommodation_id, keys_to_add)

    # 5) Respuesta
    acc = get_accommodation(db, accommodation_id)
    _attach_presigned_urls(acc)
    return acc



# ------- DELETE -------
@router.delete(
    "/{accommodation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an accommodation",
    responses={204: {"description": "Deleted. No content."}, 404: {"model": ErrorResponse}},
    operation_id="deleteAccommodation",
)
def delete_accommodation_endpoint(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    acc = get_accommodation(db, accommodation_id)
    if acc.host_id != user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    delete_accommodation(db, accommodation_id)
    return None
