# app/core/s3.py
import boto3
from botocore.config import Config
from .config import settings

def get_s3():
    session = boto3.session.Session()
    s3 = session.client(
        "s3",
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        endpoint_url=settings.S3_ENDPOINT,  # clave para MinIO
        use_ssl=settings.S3_USE_SSL,
        config=Config(
            s3={
                "addressing_style": "path",  # MinIO funciona perfecto así
                "signature_version": "s3v4",
            },
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=5, read_timeout=30,
        ),
    )
    return s3
