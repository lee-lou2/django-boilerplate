import os

from celery import Celery

from conf.schedules import CELERY_BEAT_SCHEDULE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings.local")

app = Celery("conf")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
app.autodiscover_tasks()
app.conf.timezone = "Asia/Seoul"
