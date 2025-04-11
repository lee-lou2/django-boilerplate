from celery.schedules import crontab


CELERY_BEAT_SCHEDULE = {
    # '매시간' 마다 만료된 파일 삭제
    "delete_expired_s3_files": {
        "task": "apps.file.v1.tasks.task_delete_expired_files",
        "schedule": crontab(minute="0", hour="*"),
    },
}
