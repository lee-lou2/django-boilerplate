from django.urls import path

from apps.short_url.v1.views import ShortUrlRedirectView

urlpatterns = [
    path("<str:short_key>/", ShortUrlRedirectView.as_view(), name="short-url-redirect"),
]
