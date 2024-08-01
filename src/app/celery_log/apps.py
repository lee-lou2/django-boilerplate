from django.apps import AppConfig


class CeleryLogConfig(AppConfig):
    name = "app.celery_log"

    def ready(self):
        import app.celery_log.signals
