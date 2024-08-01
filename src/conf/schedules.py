from datetime import timedelta

from celery.schedules import crontab
from django.urls import path

CELERY_BEAT_SCHEDULE = dict(
    # crontab_schedule={
    #     "task": "app.test.tasks.test_task",
    #     "schedule": crontab(hour="0", minute="0"),  # 매시간마다
    # },
    # timedelta_schedule={
    #     "task": "app.celery_log.tasks.my_task",
    #     "schedule": timedelta(seconds=5),  # 5초 간격
    #     "args": (1, 2),
    # },
)
