from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

from apps.file.models import File, FileStatus
from apps.file.v1.filters import FileFilterSet
from apps.file.v1.serializers import (
    FileUploadSerializer,
    FileDownloadSerializer,
    FileUpdateSerializer,
    FileDownloadPresignedSerializer,
)


class FileViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
):
    """파일 업로드 뷰셋"""

    queryset = File.objects.exclude(status=FileStatus.DELETE)
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = FileFilterSet
    throttle_scope = "file"

    def get_throttles(self):
        """요청 속도 제한 설정"""
        if self.action in ["create", "partial_update", "presigned"]:
            self.throttle_scope = f"{self.throttle_scope}:{self.action}"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        """쿼리셋 조회"""
        now = timezone.now()
        return (
            super()
            .get_queryset()
            .filter(
                user=self.request.user,
                expire_at__gt=now,
            )
        )

    def get_serializer_class(self):
        """시리얼라이저 클래스 설정"""
        if self.action == "partial_update":
            return FileUpdateSerializer
        elif self.action == "presigned":
            return FileDownloadPresignedSerializer
        elif self.action == "list":
            return FileDownloadSerializer
        return super().get_serializer_class()

    @extend_schema(
        request=FileUploadSerializer,
        responses={
            201: FileUploadSerializer,
        },
        tags=["file"],
        summary="파일 생성, 프리사인드 생성",
        description="""
        파일의 기본 정보를 저장합니다
        파일 업로드를 위한 프리사인드 URL을 생성합니다
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PUT method not allowed")

    @extend_schema(
        request=FileUpdateSerializer,
        responses={
            200: FileUpdateSerializer,
        },
        tags=["file"],
        summary="파일 상태 변경",
        description="""
        프리사인드 URL을 이용하여 파일을 업로드한 후
        파일의 상태를 변경합니다
        """,
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=FileDownloadSerializer,
        responses={
            200: FileDownloadSerializer,
        },
        tags=["file"],
        summary="파일 다운로드 리스트 조회",
        description="""
        지정한 콘텐츠의 파일 리스트를 출력합니다
        """,
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        request=FileDownloadPresignedSerializer,
        responses={
            200: FileDownloadPresignedSerializer,
        },
        tags=["file"],
        summary="파일 다운로드, 프리사인드 생성",
        description="""
        파일 다운로드를 위한 프리사인드 URL을 생성합니다
        """,
    )
    @action(
        detail=True, methods=["POST"], serializer_class=FileDownloadPresignedSerializer
    )
    def presigned(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
