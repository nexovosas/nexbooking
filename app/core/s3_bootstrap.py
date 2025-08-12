from botocore.exceptions import ClientError
from .config import settings
from .s3 import get_s3

def ensure_bucket():
    s3 = get_s3()
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=settings.S3_BUCKET)
