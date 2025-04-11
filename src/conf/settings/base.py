import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from common.enums.base import DjangoEnvironment
from conf.utils import load_aws_parameters

# 파이썬 버전 확인
if sys.version_info.major != 3 or sys.version_info.minor != 12:
    raise RuntimeError("파이썬 버전이 올바르지 않습니다")

# 프로젝트 설정
PROJECT_NAME = "django_boilerplate"

# 기본 설정
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SERVER
DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE")
DJANGO_ENVIRONMENT = DJANGO_SETTINGS_MODULE.split(".settings.")[1]
if DJANGO_ENVIRONMENT not in [env.value for env in DjangoEnvironment]:
    raise ValueError("Invalid DJANGO_ENVIRONMENT")

# .env 로드
load_dotenv()

# AWS 설정
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME")

# AWS 파라미터 스토어 조회(1회 실행)
if DJANGO_ENVIRONMENT not in [
    DjangoEnvironment.LOCAL.value,
    DjangoEnvironment.TEST.value,
] and not os.environ.get("LOADED_SETTINGS"):
    load_aws_parameters(f"/{PROJECT_NAME}/{DJANGO_ENVIRONMENT}", AWS_REGION_NAME)

# 기본 설정
SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG") == "True"

# 허용 호스트
ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1"]

# 로컬 앱 추가
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

# 외부 앱 추가
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
    "corsheaders.middleware.CorsMiddleware",  # CORS 설정
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_hosts.middleware.HostsRequestMiddleware",  # 호스트 분리
    "debug_toolbar.middleware.DebugToolbarMiddleware",  # 디버깅을 위한 도구
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Static 서버 없이 파일 처리
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

# 데이터베이스 마이그레이션 설정
# [How]
# - 모델 구현 시 Meta 클래스에 database 속성 추가
# - 예) class Meta: database = "statistics"
# - 이렇게 추가 후 DATABASE_APPS_MAPPING_FOR_MIGRATIONS 에 추가하면
#   해당 모델은 지정한 데이터베이스로 마이그레이션 됨
DATABASE_APPS_MAPPING_FOR_MIGRATIONS = {}

# 데이터베이스 라우터
DATABASE_ROUTERS = ["conf.routers.DefaultRouter"]

# 캐시
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

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
AUTH_USER_MODEL = "user.User"  # 기본 유저 모델

# EMAIL
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"  # 이메일 백엔드
EMAIL_HOST = os.environ.get("EMAIL_HOST")  # 이메일 호스트
EMAIL_PORT = int(os.environ.get("EMAIL_PORT"))  # 이메일 포트
EMAIL_USE_TLS = True  # TLS 사용 여부
EMAIL_USE_SSL = False  # SSL 사용 여부
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")  # 이메일 호스트 유저
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")  # 이메일 호스트 패스워드

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")  # 기본 발송 이메일 주소

# 언어 및 시간 설정
LANGUAGE_CODE = "ko"  # 언어 코드
TIME_ZONE = "Asia/Seoul"  # 시간대
USE_I18N = True  # 다국어 지원
USE_TZ = True  # 시간대 사용(데이터 저장 시 UTC로 저장, 조회 시 TIME_ZONE으로 변환)

# APPEND_SLASH
APPEND_SLASH = False  # 슬래시 추가 여부

# STATIC
STATIC_URL = "/static/"  # 정적 파일 URL
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # 정적 파일 루트
STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"  # 정적 파일 저장소
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# HOST
DEFAULT_HOST = "api"  # 기본 호스트
ROOT_HOSTCONF = "conf.hosts"  # 호스트 설정
ROOT_URLCONF = "conf.urls.api"  # URL 설정

# DRF
REST_FRAMEWORK = {
    "COERCE_DECIMAL_TO_STRING": False,
    # 기본 인증 클래스 설정
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "conf.authentications.JWTLazyUserAuthentication",
    ],
    # 기본 퍼미션 클래스 설정
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    # 기본 랜더러 클래스 설정
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    # 예외 핸들러 설정
    "EXCEPTION_HANDLER": "conf.exceptions.default_exception_handler",
    # 필터 백엔드 설정
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    # 기본 페이지네이션 클래스 설정
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    # 기본 스키마 클래스 설정
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # 테스트 요청 포맷 설정
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    # 기본 캐시 설정
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


# SIMPLE JWT 설정
SIMPLE_JWT = {
    # 토큰 만료 시간 설정
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # 리프래시 토큰 교체 여부
    "ROTATE_REFRESH_TOKENS": False,
    # 블랙리스트 설정
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    # 알고리즘 설정
    "ALGORITHM": "HS256",
    # 토큰 시크릿 키 설정
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    # ISSUER 설정
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

# Sentry(1회 실행)
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
EMAIL_VERIFICATION_TIMEOUT = 60 * 10  # 이메일 검증 토큰 만료 시간 10분
EMAIL_VERIFICATION_HASH_SALT = os.environ.get("EMAIL_VERIFICATION_HASH_SALT", "")
SIGNUP_CONFIRM_URL = os.environ.get("SIGNUP_CONFIRM_URL")
RESET_PASSWORD_URL = os.environ.get("RESET_PASSWORD_URL")
SIGNUP_COMPLETED_URL = os.environ.get("SIGNUP_COMPLETED_URL")

# 개인정보 암호키
USER_ENCRYPTION_KEY = os.environ.get("USER_ENCRYPTION_KEY", "")

# 소셜 로그인 - 구글
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

# 한 번 실행이 필요한 로직 예외용
os.environ.setdefault("LOADED_SETTINGS", "True")

# 출석 체크 정책
ATTENDANCE_CHECK_REWARD_POINTS = list(
    map(
        lambda x: int(x),
        os.environ.get("ATTENDANCE_CHECK_REWARD_POINTS", "5,5,5,10,10,10,100").split(
            ","
        ),
    )
)
