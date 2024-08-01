from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class FileStatus(models.IntegerChoices):
    """파일 상태"""

    WAIT = 0, "대기"
    DONE = 1, "완료"
    FAIL = 2, "실패"
    DELETE = 3, "삭제"


class File(models.Model):
    """파일"""

    file_id = models.UUIDField(verbose_name="파일 ID", primary_key=True)
    file_name = models.CharField(max_length=100, verbose_name="파일명")
    file_size = models.IntegerField(default=0, verbose_name="파일 크기")
    object_key = models.CharField(max_length=255, verbose_name="파일 URL")
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="file",
        null=True,
    )
    status = models.PositiveSmallIntegerField(
        choices=FileStatus.choices,
        verbose_name="파일 상태",
        default=FileStatus.WAIT,
    )

    content_label = models.CharField(
        max_length=50, verbose_name="컨텐츠 레이블", blank=True, default=""
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="file", null=True
    )
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(verbose_name="생성일시", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="수정일시", auto_now=True)

    class Meta:
        db_table = "file"
        verbose_name = "파일"
        verbose_name_plural = verbose_name
