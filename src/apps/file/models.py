from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from uuid_extensions import uuid7


class FileStatus(models.IntegerChoices):
    """파일 상태"""

    READY = 1, "준비"
    GENERATED = 2, "생성 완료"
    SUCCESS_UPLOAD = 3, "업로드 성공"
    FAIL_UPLOAD = 4, "업로드 실패"
    DELETE = 5, "삭제"


class FileContentType(models.IntegerChoices):
    """파일 타입"""

    OTHER = 1, "기타"
    QNA = 2, "QnA"


class File(models.Model):
    """파일"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="저장에 사용되는 파일 ID",
    )
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="files",
    )
    file_name = models.CharField(
        max_length=100,
        verbose_name="실제 파일명",
    )
    extension = models.CharField(
        max_length=10,
        verbose_name="파일 확장자",
    )
    file_size = models.IntegerField(
        default=0,
        verbose_name="파일 크기",
    )
    object_key = models.TextField(
        verbose_name="파일 URL",
        null=True,
        blank=True,
    )
    # [Why]
    # Q. ContentType, ObjectId를 사용한 이유는?
    # A. 파일은 주로 특정 객체에 연결되어 사용되며, 이 객체는 다양한 모델일 수 있음
    #    따라서, GenericForeignKey를 사용하여 다양한 모델과 연결할 수 있도록 함
    # Q. nullable 한 이유는?
    # A. 파일이 특정 객체에 연결되지 않을 수도 있음
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        related_name="files",
        null=True,
        verbose_name="컨텐츠 타입",
    )
    object_id = models.CharField(
        max_length=36,
        null=True,
        verbose_name="컨텐츠 ID",
    )
    content_object = GenericForeignKey("content_type", "object_id")
    status = models.PositiveSmallIntegerField(
        choices=FileStatus,
        verbose_name="파일 상태",
        default=FileStatus.READY,
    )
    expire_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="만료일시",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 일시",
    )

    class Meta:
        db_table = "file"
        verbose_name = "파일"
        verbose_name_plural = verbose_name
        # [Why]
        # Q. ContentType, ObjectId를 복합 키로 설정한 이유는?
        # A. 항상 두 값이 함께 사용되며, 이 조합이 유일한 값을 보장하기 때문
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


# [Why]
# Q. FileDownloadHistory 모델을 만든 이유는?
# A. 파일 다운로드 이력을 저장하기 위해
# Q. 어떤 정보를 저장하는가?
# A. 다운로드를 요청한 사용자, 다운로드 사유, 다운로드한 파일, 생성일시
class FileDownloadHistory(models.Model):
    """파일 다운로드 이력"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="file_download_history",
    )
    reason = models.CharField(
        max_length=100,
        verbose_name="다운로드 사유",
        null=True,
        blank=True,
    )
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name="download_history",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일시",
    )

    class Meta:
        db_table = "file_download_history"
        verbose_name = "파일 다운로드 이력"
        verbose_name_plural = verbose_name
