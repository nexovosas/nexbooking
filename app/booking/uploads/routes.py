# app/uploads/routes.py
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from app.core.s3 import get_s3_client
from app.core.config import settings
from app.auth import verify_token  # protege con JWT

router = APIRouter(prefix="/uploads", tags=["Uploads"])

PRESIGNED_GET_EXPIRES = 3600   # 1h
PRESIGNED_POST_EXPIRES = 600   # 10min

def _user_namespace(user_id: int, folder: str) -> str:
    folder = (folder or "uploads").strip("/ ")
    return f"users/{user_id}/{folder}"

@router.post("/file", status_code=status.HTTP_201_CREATED)
async def upload_server_side(
    file: UploadFile = File(..., description="Archivo a subir"),
    folder: str = Query("uploads", description="Carpeta lógica"),
    s3 = Depends(get_s3_client),
    user = Depends(verify_token),
):
    if not file.content_type:
        raise HTTPException(400, "Content-Type requerido")

    key = f"{_user_namespace(user['id'], folder)}/{uuid4()}-{file.filename}"
    try:
        s3.upload_fileobj(
            file.file,
            settings.S3_BUCKET,
            key,
            ExtraArgs={"ContentType": file.content_type},  # no uses ACL en MinIO
        )
    except Exception as e:
        raise HTTPException(500, f"Error subiendo a S3: {e!s}")

    presigned_get = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": key,
            # Opcional: forzar descarga con nombre
            # "ResponseContentDisposition": f'attachment; filename="{file.filename}"'
        },
        ExpiresIn=PRESIGNED_GET_EXPIRES,
    )
    return {"bucket": settings.S3_BUCKET, "key": key, "presigned_get": presigned_get, "expires_in": PRESIGNED_GET_EXPIRES}

@router.post("/presign")
def create_presigned_post(
    filename: str,
    content_type: str,
    folder: str = Query("uploads"),
    max_size: int = Query(10_000_000, ge=1, le=50_000_000),
    s3 = Depends(get_s3_client),
    user = Depends(verify_token),
):
    key = f"{_user_namespace(user['id'], folder)}/{uuid4()}-{filename}"
    try:
        presigned = s3.generate_presigned_post(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, max_size],
                ["starts-with", "$key", _user_namespace(user['id'], folder)],  # restringe prefijo
            ],
            ExpiresIn=PRESIGNED_POST_EXPIRES,
        )
    except Exception as e:
        raise HTTPException(500, f"Error generando presigned POST: {e!s}")

    # también devolvemos un GET temporal para usar tras la subida
    presigned_get = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=PRESIGNED_GET_EXPIRES,
    )
    return {
        "key": key,
        "upload_url": presigned["url"],
        "upload_fields": presigned["fields"],
        "presigned_get": presigned_get,
        "expires_in": {"post": PRESIGNED_POST_EXPIRES, "get": PRESIGNED_GET_EXPIRES},
        "max_size": max_size,
    }

@router.get("/url")
def presigned_download_url(
    key: str = Query(..., description="Key exacta en el bucket"),
    as_attachment: bool = Query(False, description="Forzar descarga"),
    s3 = Depends(get_s3_client),
    user = Depends(verify_token),
):
    # Seguridad básica: que solo acceda a su propio namespace
    ns = f"users/{user['id']}/"
    if not key.startswith(ns):
        raise HTTPException(403, "No autorizado para acceder a este recurso")

    params = {"Bucket": settings.S3_BUCKET, "Key": key}
    if as_attachment:
        filename = key.split("/")[-1]
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

    url = s3.generate_presigned_url("get_object", Params=params, ExpiresIn=PRESIGNED_GET_EXPIRES)
    return {"url": url, "expires_in": PRESIGNED_GET_EXPIRES}

@router.delete("")
def delete_object(
    key: str = Query(..., description="Key exacta en el bucket"),
    s3 = Depends(get_s3_client),
    user = Depends(verify_token),
):
    ns = f"users/{user['id']}/"
    if not key.startswith(ns):
        raise HTTPException(403, "No autorizado para borrar este recurso")
    try:
        s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)
    except Exception as e:
        raise HTTPException(500, f"Error eliminando objeto: {e!s}")
    return {"deleted": True, "key": key}
