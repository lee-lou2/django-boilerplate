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

# Toggle debugging mode
if settings.DEBUG:
    urlpatterns += debug_toolbar_urls()

# Allow admin page access only in the local environment
if settings.DJANGO_ENVIRONMENT == DjangoEnvironment.LOCAL.value:
    urlpatterns += [
        path("admin/", admin.site.urls),
    ]

# Allow API documentation access only in local, develop, and stage environments
if settings.DJANGO_ENVIRONMENT in [
    DjangoEnvironment.LOCAL.value,
    DjangoEnvironment.DEVELOP.value,
    DjangoEnvironment.STAGE.value,
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
