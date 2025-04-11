import mimetypes
import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

S3_CLIENT = None
try:
    S3_CLIENT = boto3.client(
        "s3",
        region_name=getattr(settings, "AWS_S3_REGION_NAME", "ap-northeast-2"),
        config=Config(
            signature_version=getattr(settings, "AWS_S3_SIGNATURE_VERSION", "s3v4"),
        ),
    )
    logger.info("Successfully initialized S3 client.")
except Exception as e:
    logger.error(f"Error initializing S3 client: {e}", exc_info=True)


def generate_upload_presigned_url(
    object_key: str,
    file_size: int = 0,  # 기본 파일 크기
    expires_in: int = 300,  # 기본 만료 시간 (초)
) -> dict:
    """
    S3 업로드용 Presigned POST URL 생성

    Args:
        object_key (str): S3에 저장될 객체 키 (파일 경로 및 이름)
        file_size (int): 예상 파일 크기 (바이트 단위). content-length-range 조건에 사용됨.
        expires_in (int): Presigned URL의 유효 시간 (초)

    Returns:
        dict: Presigned POST URL 및 필드 정보
        None: 클라이언트가 없거나 오류 발생 시
    """
    if not S3_CLIENT:
        logger.error("S3 client is not available for generating upload presigned URL.")
        return {}
    # 파일 확장자로부터 Content-Type 조회
    content_type, _ = mimetypes.guess_type(object_key)
    if not content_type:
        content_type = "application/octet-stream"
        logger.warning(
            f"Could not guess Content-Type for {object_key}. Defaulting to {content_type}."
        )
    max_upload_size = (file_size if file_size > 0 else 100 * 1024 * 1024) + (
        10 * 1024 * 1024
    )
    fields = {"Content-Type": content_type}
    conditions = [
        {"Content-Type": content_type},
        ["content-length-range", 0, max_upload_size],
    ]
    try:
        response = S3_CLIENT.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=object_key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expires_in,
        )
        return response
    except ClientError as e:
        logger.error(
            f"Error generating upload presigned URL for {object_key}: {e}",
            exc_info=True,
        )
        return {}
    except Exception as e:
        # 기타 예외 발생 시 로깅
        logger.error(
            f"Unexpected error generating upload presigned URL for {object_key}: {e}",
            exc_info=True,
        )
        return {}


def generate_download_presigned_url(
    object_key: str,
    expires_in: int = 300,  # 기본 만료 시간 (초)
) -> dict:
    """
    S3 다운로드용 Presigned URL 생성 (공유 클라이언트 사용)

    Args:
        object_key (str): 다운로드할 S3 객체 키
        expires_in (int): Presigned URL의 유효 시간 (초)

    Returns:
        str: Presigned GET URL
        None: 클라이언트가 없거나 오류 발생 시
    """
    if not S3_CLIENT:
        logger.error(
            "S3 client is not available for generating download presigned URL."
        )
        return {}

    try:
        response = S3_CLIENT.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,  # 버킷 이름은 settings에서 가져옴
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )
        return response
    except ClientError as e:
        logger.error(
            f"Error generating download presigned URL for {object_key}: {e}",
            exc_info=True,
        )
        return {}
    except Exception as e:
        logger.error(
            f"Unexpected error generating download presigned URL for {object_key}: {e}",
            exc_info=True,
        )
        return {}
