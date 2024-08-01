from django.urls import path, include
from rest_framework.routers import SimpleRouter

from app.file.v1.views import FileViewSet, FilePresignedViewSet

router = SimpleRouter()
router.register("presigned", FilePresignedViewSet, basename="files/presigned")
router.register("", FileViewSet, basename="files")

urlpatterns = [path("files/", include(router.urls))]
