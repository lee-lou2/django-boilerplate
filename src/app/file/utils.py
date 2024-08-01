import logging
import mimetypes

import boto3
from botocore.config import Config
from django.conf import settings


def generate_presigned(object_key):
    """프리사인드 생성"""
    s3_client = boto3.client(
        "s3",
        config=Config(
            region_name="ap-northeast-2",
            signature_version="s3v4",
        ),
    )
    content_type, _ = mimetypes.guess_type(object_key)
    resp = s3_client.generate_presigned_post(
        settings.AWS_STORAGE_BUCKET_NAME,
        object_key,
        Conditions=[
            [
                "content-length-range",
                0,
                settings.AWS_S3_MAX_UPLOAD_SIZE * 1024 * 1024,
            ],
            ["starts-with", "$Content-Type", content_type],
        ],
        ExpiresIn=settings.AWS_PRESIGNED_URL_EXPIRES,
    )
    return resp.get("url"), resp.get("fields")


def has_file_in_s3(object_key: str):
    """파일 존재여부 확인"""
    s3 = boto3.client("s3")
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    try:
        s3.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return False
