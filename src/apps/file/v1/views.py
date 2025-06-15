from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins, exceptions
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
    """File Upload ViewSet"""

    queryset = File.objects.exclude(status=FileStatus.DELETE)
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = FileFilterSet
    throttle_scope = "file"

    def get_throttles(self):
        """Set request rate limit"""
        if self.action in ["create", "partial_update", "presigned"]:
            self.throttle_scope = f"{self.throttle_scope}:{self.action}"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        """Retrieve queryset"""
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
        """Set serializer class"""
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
        summary="Create File, Generate Presigned URL",
        description="""
        Saves basic file information.
        Generates a presigned URL for file upload.
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
        summary="Change File Status",
        description="""
        Changes the file status after uploading the file using the presigned URL.
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
        summary="Retrieve File Download List",
        description="""
        Outputs the list of files for the specified content.
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
        summary="Download File, Generate Presigned URL",
        description="""
        Generates a presigned URL for file download.
        """,
    )
    @action(
        detail=True, methods=["POST"], serializer_class=FileDownloadPresignedSerializer
    )
    def presigned(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
