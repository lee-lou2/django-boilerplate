from django.db import models


class CeleryLogStatus(models.TextChoices):
    """샐러리 상태"""

    PENDING = "PENDING", "대기"
    SUCCESS = "SUCCESS", "성공"
    FAILURE = "FAILURE", "실패"


class CeleryLog(models.Model):
    """샐러리 로그"""

    name = models.CharField(max_length=100, verbose_name="태스크 명")
    task_id = models.CharField(max_length=36, verbose_name="태스크 ID")
    status = models.CharField(
        max_length=10,
        verbose_name="태스크 상태",
        choices=CeleryLogStatus.choices,
        default=CeleryLogStatus.PENDING,
    )
    message = models.TextField(verbose_name="메세지", blank=True, default="")
    result = models.TextField(verbose_name="결과", blank=True, default="")
    args = models.CharField(
        default=list, max_length=500, blank=True, verbose_name="태스크 args"
    )
    kwargs = models.CharField(
        default=dict, max_length=500, blank=True, verbose_name="태스크 kwargs"
    )
    created_at = models.DateTimeField(verbose_name="생성일시", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="수정일시", auto_now=True)

    class Meta:
        db_table = "celery_log"
        verbose_name = "셀러리 로그"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
