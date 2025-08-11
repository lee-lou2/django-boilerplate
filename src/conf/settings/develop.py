from conf.settings.base import *

# CORS
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = [
    # 허용 오리진 추가
]
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "postgres"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "password"),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    },
    "replica": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "postgres"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "password"),
        "HOST": os.environ.get("POSTGRES_REPLICA_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_REPLICA_PORT", "5432"),
    },
}

# LOGGING LEVEL
LOGGING["loggers"]["django"]["level"] = "INFO"
LOGGING["loggers"]["django.db.backends"]["level"] = "INFO"
LOGGING["loggers"]["default"]["level"] = "INFO"
