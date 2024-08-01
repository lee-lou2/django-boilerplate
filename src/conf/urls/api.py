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

from conf.enums import DjangoEnvironment

urlpatterns = [
    path("v1/", include("app.user.v1.urls")),
    path("v1/", include("app.verifier.v1.urls")),
    path("_health/", lambda request: HttpResponse()),
]

urlpatterns += [
    path(
        "openapi.json/",
        SpectacularJSONAPIView.as_view(patterns=urlpatterns),
        name="schema",
    ),
    path("swagger/", SpectacularSwaggerView.as_view(), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(), name="redoc"),
]

# 디버깅 모드 전환
if settings.DEBUG:
    urlpatterns += debug_toolbar_urls()

# 로컬 환경에서만 admin 페이지 접근 가능
if settings.DJANGO_ENVIRONMENT == DjangoEnvironment.LOCAL.value:
    urlpatterns += [
        path("admin/", admin.site.urls),
    ]
