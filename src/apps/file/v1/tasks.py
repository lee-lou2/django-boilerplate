from django.utils import timezone

from apps.file.models import FileStatus, File
from conf.celery import app


@app.task
def task_delete_expired_files():
    """만료 파일 삭제"""
    expired_files = File.objects.exclude(
        status=FileStatus.DELETE,
    ).filter(
        expire_at__lt=timezone.now(),
    )
    for expired_file in expired_files:
        # 파일 삭제
        ...
        # 상태 변경
        expired_file.status = FileStatus.DELETE
        expired_file.save(update_fields=["status"])
    return f"{expired_files.count()} files deleted"
