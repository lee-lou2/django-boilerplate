import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from conf.enums import DjangoEnvironment


# 파이썬 버전 확인
if sys.version_info.major != 3 or sys.version_info.minor != 10:
    raise RuntimeError("파이썬 버전이 올바르지 않습니다")

# .env 로드
load_dotenv()

# 기본 설정
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SERVER
DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE")
DJANGO_ENVIRONMENT = DJANGO_SETTINGS_MODULE.split(".settings.")[1]
if DJANGO_ENVIRONMENT not in [env.value for env in DjangoEnvironment]:
    raise ValueError("Invalid DJANGO_ENVIRONMENT")

# PROJECT
PROJECT_NAME = "djagno-boilerplate"
SITE_NAME = "djagno-boilerplate"
SITE_LOGO = "img/logo.png"
DOMAIN = "domain.com"

SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG") == "True"

# 허용 호스트
ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1"]

# 로컬 앱 추가
LOCAL_APPS = [
    "app.common",
    "app.celery_log",
    "app.user",
    "app.device",
    "app.withdrawal_user",
    "app.log",
    "app.verifier",
    "app.file",
]

# 외부 앱 추가
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "django_hosts",
    "django_celery_beat",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "debug_toolbar",
    "django_celery_results",
]

# 기본 앱 추가
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

INSTALLED_APPS = LOCAL_APPS + THIRD_PARTY_APPS + DJANGO_APPS

# 미들웨어 설정
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "conf.routers.DBRouterMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django_hosts.middleware.HostsRequestMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# 템플릿 설정
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

# 데이터베이스 설정
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

# 데이터베이스 라우터
DATABASE_ROUTERS = ["conf.routers.DefaultRouter"]

# 패스워드 유효성 검사
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# AUTH_USER_MODEL
AUTH_USER_MODEL = "user.User"

# EMAIL
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT"))
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

# 언어 및 시간 설정
LANGUAGE_CODE = "ko"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# APPEND_SLASH
APPEND_SLASH = False

# STATIC
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# HOST
DEFAULT_HOST = "api"
ROOT_HOSTCONF = "conf.hosts"
ROOT_URLCONF = "conf.urls.api"

# DRF
REST_FRAMEWORK = {
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "EXCEPTION_HANDLER": "conf.exceptions.default_exception_handler",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_SCHEMA_CLASS": "conf.openapi.CustomAutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "NON_FIELD_ERRORS_KEY": "non_field",
}


# SIMPLE JWT 설정
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
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
    "TITLE": f"{SITE_NAME} API",
    "DESCRIPTION": f"""개발: [api.dev.{DOMAIN}](https://api.dev.{DOMAIN})<br/>운영: [api.{DOMAIN}](https://api.{DOMAIN})""",
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
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "Bearer": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": "/v1/user/login/",
                    },
                },
            },
        },
    },
    "SECURITY": [{"Bearer": []}],
    "PREPROCESSING_HOOKS": [
        "conf.spectacular_hooks.api_ordering",
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
}

# CELERY
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_ENABLE_UTC = False
CELERY_TIMEZONE = "Asia/Seoul"
CELERYD_SOFT_TIME_LIMIT = 300
CELERYD_TIME_LIMIT = CELERYD_SOFT_TIME_LIMIT + 60
CELERY_TASK_IGNORE_RESULT = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

SIMPLE_JWT_ALGORITHM = "HS256"
SOCIAL_REDIRECT_PATH = "/accounts/login/"

# KAKAO
KAKAO_CLIENT_ID = "**"
KAKAO_CLIENT_SECRET = "**"
KAKAO_LOGIN_URL = "https://kauth.kakao.com/oauth/authorize?response_type=code&client_id={kakao_client_id}&redirect_uri={SOCIAL_REDIRECT_URL}&state=kakao"

# NAVER
NAVER_CLIENT_ID = "**"
NAVER_CLIENT_SECRET = "**"
NAVER_LOGIN_URL = "https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id={naver_client_id}&redirect_uri={SOCIAL_REDIRECT_URL}&state=naver"

# FACEBOOK
FACEBOOK_CLIENT_ID = "**"
FACEBOOK_CLIENT_SECRET = "**"
FACEBOOK_LOGIN_URL = "https://www.facebook.com/v9.0/dialog/oauth?response_type=code&client_id={facebook_client_id}&redirect_uri={SOCIAL_REDIRECT_URL}&state=facebook"

# GOOGLE
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_LOGIN_URL = "https://accounts.google.com/o/oauth2/auth/oauthchooseaccount?response_type=code&client_id={google_client_id}&redirect_uri={SOCIAL_REDIRECT_URL}&state=google&scope=openid"

# APPLE
APPLE_CLIENT_ID = "**"
APPLE_CLIENT_SECRET = """-----BEGIN PRIVATE KEY-----
**
-----END PRIVATE KEY-----"""
APPLE_KEY_ID = "**"
APPLE_TEAM_ID = "**"
APPLE_LOGIN_URL = "https://appleid.apple.com/auth/authorize?response_type=code&client_id={apple_client_id}&redirect_uri={SOCIAL_REDIRECT_URL}&state=apple"

# Sentry
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
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

# AWS
AWS_S3_MAX_UPLOAD_SIZE = int(os.environ.get("AWS_S3_MAX_UPLOAD_SIZE", 20))  # MB
AWS_CLOUDFRONT_URL = os.environ.get("AWS_CLOUDFRONT_URL")
AWS_PRESIGNED_URL_EXPIRES = 300
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
