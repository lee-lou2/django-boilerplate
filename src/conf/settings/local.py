from conf.settings.base import *

# CELERY
CELERY_BROKER_URL = "redis://localhost:6379/0"

# LOGGING LEVEL
LOGGING["loggers"]["django"]["level"] = "INFO"
LOGGING["loggers"]["django.db.backends"]["level"] = "INFO"
LOGGING["loggers"]["default"]["level"] = "DEBUG"
