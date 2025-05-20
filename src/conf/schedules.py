from celery.schedules import crontab


CELERY_BEAT_SCHEDULE = {
    # Delete expired files every hour
    "delete_expired_s3_files": {
        "task": "apps.file.v1.tasks.task_delete_expired_files",
        "schedule": crontab(minute="0", hour="*"),
    },
}
