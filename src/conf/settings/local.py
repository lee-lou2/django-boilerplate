from conf.settings.base import *

# 로컬 이메일 발송
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# LOGGING LEVEL
LOGGING["loggers"]["django"]["level"] = "INFO"
LOGGING["loggers"]["django.db.backends"]["level"] = "INFO"
LOGGING["loggers"]["default"]["level"] = "DEBUG"

SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(days=30)
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(days=365)
