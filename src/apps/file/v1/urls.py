from rest_framework_nested import routers

from apps.file.v1.views import FileViewSet

router = routers.SimpleRouter()
router.register("file", FileViewSet, basename="file")

urlpatterns = router.urls
