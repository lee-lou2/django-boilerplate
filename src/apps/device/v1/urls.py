from django.urls import path, include
from rest_framework_nested import routers

from apps.device.v1.views import DeviceViewSet, PushTokenViewSet

device_router = routers.SimpleRouter()
device_router.register("device", DeviceViewSet, basename="device")

push_token_router = routers.NestedSimpleRouter(
    device_router, r"device", lookup="device"
)
push_token_router.register(
    r"push_token", PushTokenViewSet, basename="device-push-token"
)

urlpatterns = [
    path("", include(device_router.urls)),
    path("", include(push_token_router.urls)),
]
