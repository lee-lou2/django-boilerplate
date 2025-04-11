from conf.settings.base import *

# CORS
CORS_ALLOWED_ORIGINS = [
    # 허용 오리진 추가
]

# LOGGING LEVEL
LOGGING["loggers"]["django"]["level"] = "INFO"
LOGGING["loggers"]["django.db.backends"]["level"] = "INFO"
LOGGING["loggers"]["default"]["level"] = "INFO"
