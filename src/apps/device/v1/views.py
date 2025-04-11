from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from apps.device.models import Device
from apps.device.v1.serializers import DeviceSerializer, PushTokenSerializer


class DeviceViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    """디바이스"""

    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        request=DeviceSerializer,
        responses={
            201: DeviceSerializer,
        },
        tags=["device"],
        summary="사용자 디바이스 생성",
        description="""
        로그인한 사용자의 디바이스를 생성합니다.
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class PushTokenViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    """푸시 토큰"""

    serializer_class = PushTokenSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        device = get_object_or_404(Device, uuid=self.kwargs["device_uuid"])
        serializer.save(device=device)

    @extend_schema(
        request=PushTokenSerializer,
        responses={
            201: PushTokenSerializer,
        },
        tags=["device"],
        summary="사용자 푸시 토큰 생성",
        description="""
        로그인한 사용자의 푸시 토큰을 생성합니다.
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
