from rest_framework.routers import SimpleRouter

from apps.short_url.v1.views import ShortUrlViewSet

router = SimpleRouter()
router.register("short-url", ShortUrlViewSet, basename="short-url")

urlpatterns = router.urls
