
import mimetypes, uuid
from typing import Optional
from botocore.exceptions import ClientError
from fastapi import UploadFile
from app.core.s3 import get_s3
from app.core.config import settings

def _join_path(*parts: Optional[str]) -> str:
    return "/".join(p.strip("/") for p in parts if p and p.strip("/"))

class S3Service:
    def __init__(self, base_prefix: str | None = None):
        self.s3 = get_s3()
        self.bucket = settings.S3_BUCKET
        self.base_prefix = (base_prefix or settings.S3_PREFIX).strip("/")
        
    # Normaliza el nombre del archivo para evitar colisiones
    # y asegura que tenga una extensión válida
    # Ejemplo: "uploads/1234567890abcdef1234567890abcdef.jpg"
    # Si no hay extensión, usa un UUID como nombre
    def _normalize_key(self, folder: str, filename: str) -> str:
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        name = uuid.uuid4().hex + (f".{ext}" if ext else "")
        return _join_path(self.base_prefix, folder, name)

    # Sube un archivo al bucket S3
    # Retorna un diccionario con la clave del objeto y la URL presignada
    # El archivo se cierra automáticamente después de la carga
    def upload_file(self, file: UploadFile, folder: str = "") -> dict:
        key = self._normalize_key(folder, file.filename)
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        self.s3.upload_fileobj(file.file, self.bucket, key, ExtraArgs={"ContentType": content_type, "ACL": "private"})
        file.file.close()
        return {"key": key}

    # Genera una URL presignada para subir un archivo
    # Si no se especifica 'key', usa un UUID como nombre
    # Permite especificar el tipo de contenido para la carga
    # Retorna un diccionario con la clave, URL y método HTTP
    # Ejemplo: {"key": "uploads/1234567890abcdef1234567890abcdef.jpg", "url": "https://...", "method": "PUT"}
    def presign_put_url(self, key: Optional[str] = None, folder: str = "", content_type: str = "application/octet-stream") -> dict:
        if not key:
            key = self._normalize_key(folder, "blob")
        url = self.s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=settings.S3_PRESIGNED_EXPIRES,
        )
        return {"key": key, "url": url, "method": "PUT"}

    # Genera una URL presignada para obtener un objeto
    # Permite acceder al archivo sin necesidad de autenticación
    # Retorna la URL presignada para descargar el objeto
    # Ejemplo: "https://s3.nexovo.com.co/uploads/1234567890abcdef1234567890abcdef.jpg?..."
    def presign_get_url(self, key: str) -> str:
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=settings.S3_PRESIGNED_EXPIRES,
        )

    # Elimina un objeto del bucket S3
    # Si el objeto no existe, ignora el error
    # No retorna nada, solo asegura que el objeto se elimine
    def delete_object(self, key: str) -> None:
        self.s3.delete_object(Bucket=self.bucket, Key=key)
