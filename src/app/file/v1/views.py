from rest_framework import viewsets, mixins, exceptions, permissions

from app.file.models import File, FileStatus
from app.file.v1.serializers import FilePresignedSerializer, FileSerializer


class FilePresignedViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    """파일 프리사인드 생성 뷰"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FilePresignedSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FileViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
):
    """파일 뷰셋"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer
    queryset = File.objects.exclude(status=FileStatus.DELETE)

    def get_queryset(self):
        queryset = super().get_queryset()
        # 생성자만 조회 가능
        queryset = queryset.filter(user=self.request.user)
        if self.action == "update":
            # 대기중인 파일만 업데이트 가능
            return queryset.filter(status=FileStatus.WAIT)
        return queryset

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PATCH")
