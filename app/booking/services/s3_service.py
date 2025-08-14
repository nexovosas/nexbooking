from __future__ import annotations

import logging
import mimetypes
import uuid
from typing import Optional

from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.s3 import get_s3
from app.core.config import settings


def _join_path(*parts: Optional[str]) -> str:
    """Une partes de path evitando '//' y preservando jerarquía."""
    return "/".join(p.strip("/") for p in parts if p and p.strip("/"))


class S3Service:
    """
    Servicio S3/MinIO para:
      - Subir archivos (upload_file)
      - Generar URLs presignadas (PUT/GET)
      - Eliminar objetos (delete_object / delete_objects)

    Guarda/usa KEYS (no URLs públicas) para favorecer buckets privados.
    """

    def __init__(self, base_prefix: str | None = None) -> None:
        self.s3 = get_s3()  # boto3 client ya configurado por tu proyecto
        self.bucket = settings.S3_BUCKET
        # Prefijo base configurable (e.g., "uploads"); evita doble '/'
        self.base_prefix = (base_prefix or settings.S3_PREFIX or "").strip("/")

    # -----------------------
    # Helpers de generación de keys
    # -----------------------
    def _normalize_key(self, folder: str, filename: str) -> str:
        """
        Genera una key única y con extensión válida (si la hay).
        Ej.: uploads/accommodations/1/7f1a...c4.png
        """
        ext = ""
        if "." in filename:
            _ext = filename.rsplit(".", 1)[-1].lower()
            # evita extensiones raras tipo '.' al final
            ext = f".{_ext}" if _ext else ""
        name = f"{uuid.uuid4().hex}{ext}"
        return _join_path(self.base_prefix, folder, name)

    def _guess_content_type(self, filename: str, fallback: str = "application/octet-stream") -> str:
        return mimetypes.guess_type(filename)[0] or fallback

    # -----------------------
    # Subida directa (backend)
    # -----------------------
    # dentro de la clase S3Service
    def upload_file(self, file: UploadFile, folder: str = "") -> dict:
        """
        Sube el UploadFile al bucket en la ruta {base_prefix}/{folder}/{uuid.ext}.
        Asegura puntero al inicio y cierra el stream al final.
        """
        key = self._normalize_key(folder, file.filename)
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"

        # robustez: garantizamos subir desde el inicio del stream
        try:
            file.file.seek(0)
        except Exception:
            pass

        self.s3.upload_fileobj(
            file.file,
            self.bucket,
            key,
            ExtraArgs={"ContentType": content_type, "ACL": "private"},
        )
        file.file.close()
        return {"key": key}


    # -----------------------
    # Presign (cliente sube/descarga directo)
    # -----------------------
    def presign_put_url(
        self,
        key: Optional[str] = None,
        folder: str = "",
        content_type: str = "application/octet-stream",
        expires: Optional[int] = None,
    ) -> dict:
        """
        Crea una URL presignada (PUT) para que el cliente suba directo a S3.
        Retorna: {"key": "...", "url": "...", "method": "PUT"}
        """
        if not key:
            key = self._normalize_key(folder, "blob")
        try:
            url = self.s3.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
                ExpiresIn=expires or settings.S3_PRESIGNED_EXPIRES,
            )
        except ClientError as e:
            logging.error("S3 presign_put_url error: %s", e)
            raise
        return {"key": key, "url": url, "method": "PUT"}

    def presign_put_urls(
        self,
        count: int = 1,
        folder: str = "",
        content_type: str = "application/octet-stream",
        expires: Optional[int] = None,
    ) -> list[dict]:
        """Convenience: devuelve N URLs presignadas de subida."""
        return [self.presign_put_url(folder=folder, content_type=content_type, expires=expires) for _ in range(count)]

    def presign_get_url(self, key: str, expires: Optional[int] = None) -> str:
        """
        Crea una URL presignada (GET) para descargar un objeto privado.
        """
        try:
            return self.s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires or settings.S3_PRESIGNED_EXPIRES,
            )
        except ClientError as e:
            logging.error("S3 presign_get_url error: %s", e)
            raise

    # -----------------------
    # Eliminación
    # -----------------------
    def delete_objects(self, keys: list[str]) -> None:
        if not keys:
            return

        # Limpia, deduplica
        normalized: list[str] = list({k.strip() for k in keys if k and k.strip()})
        if not normalized:
            return

        # S3 permite hasta 1000 keys por batch
        for i in range(0, len(normalized), 1000):
            chunk = normalized[i : i + 1000]
            try:
                response = self.s3.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": [{"Key": k} for k in chunk], "Quiet": True},
                )
                deleted = response.get("Deleted", [])
                errors = response.get("Errors", [])
                if deleted:
                    logging.info("S3: %d objetos eliminados", len(deleted))
                if errors:
                    logging.warning("S3: errores al eliminar: %s", errors)
            except ClientError as e:
                logging.error("S3 delete_objects error: %s", e)
                raise

    # -----------------------
    # Utilidades opcionales
    # -----------------------
    def object_exists(self, key: str) -> bool:
        """Verifica existencia via HEAD (sin descargar)."""
        if not key or not key.strip():
            return False
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key.strip())
            return True
        except ClientError as e:
            # 404 Not Found u otros códigos indican que no existe o sin permisos
            if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            logging.debug("S3 head_object error: %s", e)
            return False