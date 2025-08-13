from __future__ import annotations
import json
from typing import List, Optional, Type, Union

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, Path, UploadFile, status, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.verify_token import verify_token  # normalized user dict with "id" and "role"
from app.booking.services.image_service import (
    create_image_for_accommodation_from_upload,
    create_images_for_accommodation_from_keys,
    delete_images_by_ids,
)
from app.booking.services.s3_service import S3Service
from app.db.session import get_db
from app.common.schemas import ErrorResponse

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

def _ensure_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def _parse_delete_ids(raw):
    if raw is None:
        return []
    if isinstance(raw, list):
        return [int(x) for x in raw]
    s = str(raw).strip()
    # admite "[1,2]", "1,2,3" o "14"
    try:
        j = json.loads(s)
        if isinstance(j, list):
            return [int(x) for x in j]
    except Exception:
        pass
    return [int(x) for x in s.split(",") if x.strip()]

async def _parse_updates_json_from_form(request: Request) -> Optional[str]:
    """
    Lee 'updates_json' desde form-data.
    Si Swagger lo envía como 'archivo' (blob) lo lee y decodifica;
    si viene como texto, lo devuelve tal cual.
    """
    form = await request.form()
    v = form.get("updates_json")
    if v is None:
        return None
    # Si llegó como UploadFile (filename="blob")
    if hasattr(v, "read") or hasattr(v, "file"):
        try:
            data = await v.read() if hasattr(v, "read") else v.file.read()
        except Exception:
            data = v.file.read()
        try:
            return data.decode("utf-8")
        except Exception:
            return data.decode("latin-1", errors="ignore")
    # Si llegó como texto
    return str(v)

def _attach_presigned_urls(acc):
    """
    Reemplaza en memoria (solo para respuesta) las keys S3 por presigned GET URLs.
    NO hace commit, solo muta los objetos antes de serializar.
    Acepta Accommodation o lista de Accommodation.
    """
    if acc is None:
        return acc

    s3 = S3Service()

    def _sign_image(img):
        try:
            u = getattr(img, "url", None)
            if u and isinstance(u, str) and not u.lower().startswith("http"):
                # es una key → la firmamos
                img.url = s3.presign_get_url(u)
        except Exception:
            pass

    if isinstance(acc, list):
        for a in acc:
            for img in getattr(a, "images", []) or []:
                _sign_image(img)
        return acc

    # objeto único
    for img in getattr(acc, "images", []) or []:
        _sign_image(img)
    return acc


router = APIRouter(tags=["Accommodations"], prefix="/accommodations")

MAX_IMAGES_PER_ACC = 10
MAX_FILES_CREATE = 10

def _validate_images_count(images: Optional[List[UploadFile]]):
    if not images:
        return
    if len(images) > MAX_FILES_CREATE:
        raise HTTPException(status_code=422, detail=f"Max {MAX_FILES_CREATE} images allowed")

@router.post(
    "/",
    response_model=AccommodationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new accommodation",
    description="Creates a new accommodation and optionally its images. Requires authentication.",
    operation_id="createAccommodation",
    responses={
        201: {"description": "Created"},
        400: {"model": ErrorResponse, "description": "Invalid input or business rule violation"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden (not owner)"},
        409: {"model": ErrorResponse, "description": "Conflict (e.g., duplicate name)"},
        # 422: lo documenta FastAPI por validaciones; opcional dejarlo aquí
    },
)
def create_accommodation_endpoint(
    payload: str = Form(..., description="AccommodationCreate en JSON (string)"),
    images: List[UploadFile] = File(..., description="Images for the accommodation"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    # 1) Validaciones
    acc_in = AccommodationCreate.model_validate_json(payload)
    _validate_images_count(images)

    # 2) Crear alojamiento
    acc = create_accommodation(db, acc_in, host_id=user["id"])

    # 3) Subir imágenes (service ya valida tipo + tamaño)
    for f in images or []:
        create_image_for_accommodation_from_upload(f, acc.id, db)

    return acc


@router.post(
    "/{accommodation_id}/images/presign",
    summary="Get presigned PUT URLs for direct S3 upload",
    responses={200: {"description": "OK"}},
)
def presign_accommodation_images(
    accommodation_id: int = Path(..., gt=0),
    count: int = Body(1, ge=1, le=MAX_IMAGES_PER_ACC),
    content_type: str = Body("image/jpeg"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    acc = get_accommodation(db, accommodation_id)
    if acc.host_id != user.get("id"):
        raise HTTPException(status_code=403, detail="Forbidden")

    s3 = S3Service()
    # Valida que no se exceda el cupo si todas estas se llegan a registrar
    if len(acc.images or []) + count > MAX_IMAGES_PER_ACC:
        raise HTTPException(status_code=422, detail=f"Max {MAX_IMAGES_PER_ACC} images per accommodation")

    return s3.presign_put_urls(count=count, folder=f"accommodations/{accommodation_id}", content_type=content_type)


@router.get(
    "/",
    response_model=List[AccommodationOut],
    summary="List all accommodations",
    description="Retrieves all accommodations with optional pagination.",
    responses={
        200: {"description": "Successful response"},
    },
    operation_id="listAccommodations",
)
def read_all_accommodations(db: Session = Depends(get_db)):
    return get_all_accommodations(db)

@router.get(
    "/my",
    response_model=List[AccommodationOut],
    summary="Get accommodations owned by authenticated host",
    description="Returns accommodations owned by the authenticated host.",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
    operation_id="listMyAccommodations",
)
def get_my_accommodations(
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    host_id = user.get("id")
    if host_id is None:
        raise HTTPException(status_code=401, detail="Invalid token: user id missing")
    return get_accommodations_by_host(db, host_id)

@router.get(
    "/search",
    response_model=List[AccommodationOut],
    summary="Search accommodations with filters",
    description="Searches accommodations by name, max price, and services.",
    responses={200: {"description": "Successful response"}},
    operation_id="searchAccommodations",
)
def search_accommodations(
    name: Optional[str] = Query(None, description="Filter by name"),
    location: Optional[str] = Query(None, description="Filter by location"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    services: Optional[str] = Query(None, description="Comma-separated list of services"),
    db: Session = Depends(get_db),
):
    return search_accommodations_service(db, name, location, max_price, services)

@router.get(
    "/{accommodation_id}",
    response_model=AccommodationOut,
    summary="Retrieve an accommodation by ID",
    description="Fetches a single accommodation by its unique ID.",
    responses={
        200: {"description": "Successful response"},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
    },
    operation_id="getAccommodationById",
)
def read_one_accommodation(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db),
):
    acc = get_accommodation(db, accommodation_id)

    # Convertir keys S3 a URLs presignadas SOLO para la respuesta
    s3 = S3Service()
    for img in (acc.images or []):
        if isinstance(getattr(img, "url", None), str) and not img.url.lower().startswith(("http://", "https://")):
            img.url = s3.presign_get_url(img.url)

    return acc


@router.put(
    "/{accommodation_id}",
    response_model=AccommodationOut,
    summary="Update accommodation (multipart): add/remove images and optional fields",
    description=(
        "Multipart to add new images, remove existing images, and update fields.\n"
        "- `updates_json`: JSON string matching AccommodationUpdate (optional)\n"
        "- `new_images`: files to upload (optional)\n"
        "- `delete_image_ids`: repeat field to delete multiple images\n"
        "- `new_image_keys`: S3 keys already uploaded via presigned (optional)"
    ),
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "updates_json": {
                                "type": "string",
                                "description": "JSON string of AccommodationUpdate",
                                "example": (
                                    '{"name":"La Montera Glamping","description":"Updated",'
                                    '"services":"glamping,spa","is_active":true,"type":"Hotel",'
                                    '"pet_friendly":true,"location":"San Vicente Ferrer"}'
                                ),
                            },
                            "new_images": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Upload one or more image files."
                            },
                            "delete_image_ids": {
                                "type": "array",
                                "items": {"type": "integer", "format": "int32"},
                                "description": "IDs of images to delete (repeat field)."
                            },
                            "new_image_keys": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "S3 keys already uploaded via presigned PUT."
                            },
                        },
                        "required": []
                    },
                    "encoding": {
                        "updates_json": {"contentType": "application/json"},
                        "delete_image_ids": {"style": "form", "explode": True},
                        "new_images": {"style": "form", "explode": True},
                        "new_image_keys": {"style": "form", "explode": True}
                    }
                }
            }
        }
    },
)
async def update_accommodation_endpoint(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    new_images: Optional[Union[UploadFile, List[UploadFile]]] = File(None, description="Files to upload"),
    delete_image_ids: Optional[Union[str, List[int]]] = Form(None, description="IDs to delete"),
    new_image_keys: Optional[Union[str, List[str]]] = Form(None, description="S3 keys uploaded via presigned URLs"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
    request: Request = None,
):
    # 0) Auth & ownership
    acc = get_accommodation(db, accommodation_id)
    if acc.host_id != user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # 1) updates_json (lee archivo o texto del form)
    updates_json_str = await _parse_updates_json_from_form(request)
    if updates_json_str:
        updates = AccommodationUpdate.model_validate_json(updates_json_str)
        acc = update_accommodation(db, accommodation_id, updates)

    # 2) eliminar imágenes (IDs pueden venir lista/CSV/JSON/uno)
    ids_to_delete = _parse_delete_ids(delete_image_ids)

    # 3a) normalizar archivos a subir (acepta 1 o lista + fallback desde form)
    files_to_add: List[UploadFile] = []
    if isinstance(new_images, UploadFile):
        files_to_add = [new_images]
    elif isinstance(new_images, list):
        files_to_add = [f for f in new_images if isinstance(f, UploadFile)]
    if not files_to_add:
        form = await request.form()
        form_files = form.getlist("new_images")
        files_to_add = [f for f in form_files if isinstance(f, UploadFile)]

    # 3b) normalizar keys a registrar (acepta string/list + fallback desde form)
    keys_to_add: List[str] = []
    if isinstance(new_image_keys, str):
        keys_to_add = [new_image_keys]
    elif isinstance(new_image_keys, list):
        keys_to_add = [k for k in new_image_keys if isinstance(k, str)]
    if not keys_to_add:
        form = await request.form()
        klist = form.getlist("new_image_keys")
        keys_to_add = [k.strip() for k in klist if isinstance(k, str) and k.strip()]
    # dedupe keys
    keys_to_add = list(dict.fromkeys([k.strip() for k in keys_to_add if k and k.strip()]))

    # 3c) Validación de cupo total final
    existing = len(acc.images or [])
    to_delete = len(ids_to_delete or [])
    to_add_uploads = len(files_to_add)
    to_add_keys = len(keys_to_add)
    final_count = existing - to_delete + to_add_uploads + to_add_keys
    if final_count > MAX_IMAGES_PER_ACC:
        raise HTTPException(status_code=422, detail=f"Max {MAX_IMAGES_PER_ACC} images per accommodation")

    # 4) aplicar borrado
    if ids_to_delete:
        delete_images_by_ids(db, ids_to_delete, accommodation_id)

    # 5) subir archivos nuevos (service valida tipo+tamaño)
    for f in files_to_add:
        if f and getattr(f, "filename", ""):
            create_image_for_accommodation_from_upload(f, accommodation_id, db)

    # 6) registrar keys presigned en un solo call
    if keys_to_add:
        create_images_for_accommodation_from_keys(db, accommodation_id, keys_to_add)

    # 7) retornar actualizado (con URLs firmadas)
    acc = get_accommodation(db, accommodation_id)
    _attach_presigned_urls(acc)
    return acc

@router.delete(
    "/{accommodation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an accommodation",
    description="Deletes an accommodation by its ID. Requires authentication and ownership.",
    response_model=None,
    responses={
        204: {"description": "Deleted. No content."},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden (not owner)"},
        404: {"model": ErrorResponse, "description": "Accommodation not found"},
    },
    operation_id="deleteAccommodation",
)
def delete_accommodation_endpoint(
    accommodation_id: int = Path(..., gt=0, description="Accommodation ID"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
) -> Response:
    acc = get_accommodation(db, accommodation_id)  # raises 404 if not found
    if acc.host_id != user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    delete_accommodation(db, accommodation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
