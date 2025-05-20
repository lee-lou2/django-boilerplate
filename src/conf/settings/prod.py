from conf.settings.base import *

# CORS
CORS_ALLOWED_ORIGINS = [
    # Add allowed origins here
]

# LOGGING LEVEL
LOGGING["loggers"]["django"]["level"] = "INFO"
LOGGING["loggers"]["django.db.backends"]["level"] = "INFO"
LOGGING["loggers"]["default"]["level"] = "INFO"
