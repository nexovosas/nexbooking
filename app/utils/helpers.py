from typing import Union, List, Optional
import json
from app.booking.services.s3_service import S3Service
from fastapi import UploadFile, HTTPException

MAX_IMAGES_PER_ACC = 10         # Máximo total por alojamiento
MAX_FILES_CREATE = 10          # Máximo archivos aceptados al crear

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