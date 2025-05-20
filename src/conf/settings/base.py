import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from common.enums.base import DjangoEnvironment
from conf.utils import load_aws_parameters

# Check Python version
if sys.version_info.major != 3 or sys.version_info.minor != 12:
    raise RuntimeError("Invalid Python version")

# Project configuration
PROJECT_NAME = "django_boilerplate"

# Basic settings
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SERVER
DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE")
DJANGO_ENVIRONMENT = DJANGO_SETTINGS_MODULE.split(".settings.")[1]
if DJANGO_ENVIRONMENT not in [env.value for env in DjangoEnvironment]:
    raise ValueError("Invalid DJANGO_ENVIRONMENT")

# Load .env
load_dotenv()

# AWS settings
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME")

# Retrieve AWS Parameter Store values (run once)
if DJANGO_ENVIRONMENT not in [
    DjangoEnvironment.LOCAL.value,
    DjangoEnvironment.TEST.value,
] and not os.environ.get("LOADED_SETTINGS"):
    load_aws_parameters(f"/{PROJECT_NAME}/{DJANGO_ENVIRONMENT}", AWS_REGION_NAME)

# Default settings
SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG") == "True"

# Allowed hosts
ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1"]

# Local apps
LOCAL_APPS = [
    "apps.user",
    "apps.account",
    "apps.device",
    "apps.short_url",
    "apps.feed",
    "apps.file",
    "apps.agreement",
    "apps.cms",
    "apps.game",
]

# Third-party apps
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "django_hosts",
    "drf_spectacular",
    "debug_toolbar",
    "rest_framework_simplejwt.token_blacklist",
]

# Django apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

INSTALLED_APPS = LOCAL_APPS + THIRD_PARTY_APPS + DJANGO_APPS

# Middleware configuration
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS settings
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_hosts.middleware.HostsRequestMiddleware",  # Host-based routing
    "debug_toolbar.middleware.DebugToolbarMiddleware",  # Debugging tool
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Serve files without a static server
]

# Template configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "conf.wsgi.application"

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
    "replica": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}

# Database migration configuration
# [How]
# - When implementing a model add a `database` attribute to its Meta class
# - Example: class Meta: database = "statistics"
# - After adding it, include it in DATABASE_APPS_MAPPING_FOR_MIGRATIONS so that
#   the model migrates to the specified database
DATABASE_APPS_MAPPING_FOR_MIGRATIONS = {}

# Database routers
DATABASE_ROUTERS = ["conf.routers.DefaultRouter"]

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# AUTH_USER_MODEL
AUTH_USER_MODEL = "user.User"  # Default user model

# EMAIL
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"  # Email backend
EMAIL_HOST = os.environ.get("EMAIL_HOST")  # Email host
EMAIL_PORT = int(os.environ.get("EMAIL_PORT"))  # Email port
EMAIL_USE_TLS = True  # Whether to use TLS
EMAIL_USE_SSL = False  # Whether to use SSL
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")  # Email host user
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")  # Email host password

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")  # Default from email address

# Language and time settings
LANGUAGE_CODE = "ko"  # Language code
TIME_ZONE = "Asia/Seoul"  # Time zone
USE_I18N = True  # Internationalization support
USE_TZ = True  # Enable timezone support (store in UTC, display in TIME_ZONE)

# APPEND_SLASH
APPEND_SLASH = False  # Whether to append a slash

# STATIC
STATIC_URL = "/static/"  # Static file URL
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # Static file root
STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"  # Static file storage
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# HOST
DEFAULT_HOST = "api"  # Default host
ROOT_HOSTCONF = "conf.hosts"  # Host settings
ROOT_URLCONF = "conf.urls.api"  # URL configuration

# DRF
REST_FRAMEWORK = {
    "COERCE_DECIMAL_TO_STRING": False,
    # Default authentication classes
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "conf.authentications.JWTLazyUserAuthentication",
    ],
    # Default permission classes
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    # Default renderer classes
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    # Exception handler
    "EXCEPTION_HANDLER": "conf.exceptions.default_exception_handler",
    # Filter backends
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    # Default pagination class
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    # Default schema class
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Test request format
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    # Default throttle rates
    "DEFAULT_THROTTLE_RATES": {
        "feed:create": "1/second",
        "feed:like": "2/second",
        "feed:report": "2/second",
        "comment:create": "1/second",
        "comment:like": "2/second",
        "comment:report": "2/second",
        "file:create": "1/second",
        "file:update": "1/second",
        "file:presigned": "1/second",
    },
}


# SIMPLE JWT configuration
SIMPLE_JWT = {
    # Token expiration settings
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Whether to rotate refresh tokens
    "ROTATE_REFRESH_TOKENS": False,
    # Blacklist setting
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    # Algorithm setting
    "ALGORITHM": "HS256",
    # Token secret key
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    # Issuer setting
    "ISSUER": PROJECT_NAME,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

# SPECTACULAR
SPECTACULAR_SETTINGS = {
    "TITLE": f"{PROJECT_NAME} API",
    "DESCRIPTION": f"{PROJECT_NAME} API Document",
    "VERSION": "1.0.0",
    "SCHEMA_PATH_PREFIX": r"/v[0-9]",
    "DISABLE_ERRORS_AND_WARNINGS": True,
    "SORT_OPERATIONS": False,
    "SWAGGER_UI_SETTINGS": {
        "docExpansion": "none",
        "defaultModelRendering": "model",
        "defaultModelsExpandDepth": 0,
        "deepLinking": True,
        "displayRequestDuration": True,
        "persistAuthorization": True,
        "syntaxHighlight.activate": True,
        "syntaxHighlight.theme": "agate",
        "showExtensions": True,
        "filter": True,
    },
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
    "EXTENSIONS": {
        "AUTHENTICATION": [
            "conf.authentications.JWTLazyUserAuthenticationScheme",
        ],
    },
}

# Sentry (run once)
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN and os.environ.get("LOADED_SETTINGS"):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=DJANGO_ENVIRONMENT,
        traces_sample_rate=1.0,
        send_default_pii=True,
    )

# LOGGING
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(module)s | %(levelname)s | %(process)d | %(thread)d | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[%(asctime)s] %(module)s | %(levelname)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "sensitive": {
            "()": "conf.filters.SensitiveFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["sensitive"],
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django.log"),
            "formatter": "verbose",
            "filters": ["sensitive"],
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "default": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
    },
}

# Email Verification
EMAIL_VERIFICATION_TIMEOUT = 60 * 10  # Email verification token expires in 10 minutes
EMAIL_VERIFICATION_HASH_SALT = os.environ.get("EMAIL_VERIFICATION_HASH_SALT", "")
SIGNUP_CONFIRM_URL = os.environ.get("SIGNUP_CONFIRM_URL")
RESET_PASSWORD_URL = os.environ.get("RESET_PASSWORD_URL")
SIGNUP_COMPLETED_URL = os.environ.get("SIGNUP_COMPLETED_URL")

# Personal data encryption key
USER_ENCRYPTION_KEY = os.environ.get("USER_ENCRYPTION_KEY", "")

# Social login - Google
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")
GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_CLIENT_SECRETS_CONFIG = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "project_id": GOOGLE_PROJECT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI],
    }
}

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379")

# For logic that should run only once
os.environ.setdefault("LOADED_SETTINGS", "True")

# Attendance check policy
ATTENDANCE_CHECK_REWARD_POINTS = list(
    map(
        lambda x: int(x),
        os.environ.get("ATTENDANCE_CHECK_REWARD_POINTS", "5,5,5,10,10,10,100").split(
            ","
        ),
    )
)
