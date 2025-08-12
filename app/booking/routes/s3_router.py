from fastapi import APIRouter, UploadFile, File, Depends
from app.booking.services.s3_service import S3Service

router = APIRouter(prefix="/s3", tags=["s3"])

def get_service():
    return S3Service()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), s3: S3Service = Depends(get_service)):
    """
    Subida directa desde el backend (multipart/form-data)
    """
    return s3.upload_file(file)

@router.post("/presign/put")
async def create_presigned_put(folder: str = "", content_type: str = "application/octet-stream", s3: S3Service = Depends(get_service)):
    """
    Crea URL prefirmada para que el cliente suba directo a MinIO sin pasar por tu backend.
    """
    return s3.presign_put_url(folder=folder, content_type=content_type)

@router.get("/presign/get")
async def presign_get(key: str, s3: S3Service = Depends(get_service)):
    return {"url": s3.presign_get_url(key)}

@router.delete("/delete/{key}")
async def delete_object(key: str, s3: S3Service = Depends(get_service)):
    s3.delete_object(key)
    return {"ok": True}
