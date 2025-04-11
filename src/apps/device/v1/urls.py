from django.urls import path, include
from rest_framework_nested import routers

from apps.device.v1.views import DeviceViewSet, PushTokenViewSet

router = routers.SimpleRouter()
router.register("device", DeviceViewSet, basename="device")

feed_router = routers.NestedSimpleRouter(router, r"device", lookup="device")
feed_router.register(r"push_token", PushTokenViewSet, basename="device-push-token")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(feed_router.urls)),
]
