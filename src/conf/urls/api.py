from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularJSONAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from common.enums.base import DjangoEnvironment

urlpatterns = [
    path("v1/", include("apps.account.v1.urls")),
    path("v1/", include("apps.user.v1.urls")),
    path("v1/", include("apps.device.v1.urls")),
    path("v1/", include("apps.short_url.v1.urls")),
    path("v1/", include("apps.feed.v1.urls")),
    path("v1/", include("apps.file.v1.urls")),
    path("v1/", include("apps.agreement.v1.urls")),
    path("v1/", include("apps.cms.v1.urls")),
    path("v1/", include("apps.game.v1.urls")),
    path("_health/", lambda request: HttpResponse()),
]

# 디버깅 모드 전환
if settings.DEBUG:
    urlpatterns += debug_toolbar_urls()

# 로컬 환경에서만 admin 페이지 접근 가능
if settings.DJANGO_ENVIRONMENT == DjangoEnvironment.LOCAL.value:
    from apps.user.v1 import views as user_views

    from apps.user.forms import OTPAuthenticationForm

    admin.site.login_form = OTPAuthenticationForm

    urlpatterns += [
        path("admin/", admin.site.urls),
        path(
            "setup-otp/<uidb64>/<token>/", user_views.setup_otp_view, name="setup_otp"
        ),
    ]

# 로컬, 개발, 스테이지 환경에서만 API 문서 접근 가능
if settings.DJANGO_ENVIRONMENT in [
    DjangoEnvironment.LOCAL.value,
    DjangoEnvironment.DEVELOP.value,
]:
    urlpatterns += [
        path(
            "openapi.json/",
            SpectacularJSONAPIView.as_view(patterns=urlpatterns),
            name="schema",
        ),
        path("swagger/", SpectacularSwaggerView.as_view(), name="swagger-ui"),
        path("redoc/", SpectacularRedocView.as_view(), name="redoc"),
    ]
