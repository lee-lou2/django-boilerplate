from django.utils import timezone
from rest_framework import serializers

from apps.file.models import File, FileStatus, FileDownloadHistory
from apps.file.v1.utils import (
    generate_upload_presigned_url,
    generate_download_presigned_url,
)


class FileUploadSerializer(serializers.ModelSerializer):
    """
    파일 업로드 시리얼라이저:
    파일 업로드 시 직접 업로드하지 않고 프리사인드를 이용해서 업로드
    """

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), help_text="사용자"
    )
    url = serializers.CharField(
        read_only=True,
        help_text="S3 업로드 URL",
        allow_null=True,
    )
    fields = serializers.JSONField(
        read_only=True,
        help_text="S3 업로드 필드",
        allow_null=True,
    )

    def create(self, validated_data):
        instance = super().create(validated_data)
        # S3 파일 경로 저장
        content_type = ""
        file_name = f"{instance.uuid}.{instance.extension}"
        now = timezone.now()
        object_key = (
            f"files/{content_type}/{now.year}/{now.month}/{now.day}/{file_name}"
        )
        # 프리사인드 정보 추가
        # [Why]
        # Q. S3 업로드 시 프리사인드 URL을 생성하는 이유는?
        # A. 아무나, 어떤 파일이든 업로드할 수 없도록 하기 위함
        #    프리사인드를 통해 권한이 있는 사용자만 업로드할 수 있도록 함
        #    또한, 자신의 파일만 업로드할 수 있도록 하기 위함
        response = generate_upload_presigned_url(
            object_key=object_key,
            file_size=instance.file_size,
        )
        instance.object_key = object_key
        instance.status = FileStatus.GENERATED
        instance.save()
        instance.fields = response.get("fields")
        instance.url = response.get("url")
        return instance

    class Meta:
        model = File
        fields = [
            "uuid",
            "user",
            "file_name",
            "extension",
            "file_size",
            "content_type",
            "object_id",
            "status",
            "url",
            "fields",
        ]
        read_only_fields = [
            "uuid",
        ]
        extra_kwargs = {
            "user": {"write_only": True},
            "content_type": {"write_only": True},
            "object_id": {"write_only": True},
        }


class FileUpdateSerializer(serializers.ModelSerializer):
    """
    파일 업데이트 시리얼라이저:
    파일 업로드 후 상태 업데이트, 삭제 요청
    """

    class Meta:
        model = File
        fields = ["status"]


class FileDownloadSerializer(serializers.ModelSerializer):
    """
    파일 다운로드 시리얼라이저:
    파일 다운로드 가능한 파일 리스트 조회
    """

    class Meta:
        model = File
        fields = [
            "uuid",
            "file_name",
            "extension",
            "file_size",
            "content_type",
            "object_id",
            "status",
            "expire_at",
            "created_at",
        ]


class FileDownloadPresignedSerializer(serializers.ModelSerializer):
    """
    파일 다운로드 프리사인드 시리얼라이저:
    파일 다운로드 시 프리사인드를 이용해서 다운로드
    """

    reason = serializers.CharField(
        write_only=True,
        help_text="다운로드 사유",
    )
    url = serializers.CharField(
        read_only=True,
        help_text="S3 업로드 URL",
        allow_null=True,
    )
    fields = serializers.JSONField(
        read_only=True,
        help_text="S3 업로드 필드",
        allow_null=True,
    )

    def update(self, instance, validated_data):
        """파일 다운로드 프리사인드 URL 생성"""
        # [Why]
        # Q. 파일 다운로드 시 프리사인드 URL을 생성하는 이유는?
        # A. 아무나, 어떤 파일이든 다운로드할 수 없도록 하기 위함
        #    프리사인드 URL을 통해 권한이 있는 사용자만 다운로드할 수 있도록 하기 위함
        #    참고로, 모든 사람이 받아도 되는 파일은 CDN 을 통해 다운로드 가능하도록 설정
        response = generate_download_presigned_url(
            object_key=instance.object_key,
        )
        instance.fields = response.get("fields")
        instance.url = response.get("url")
        # 파일 다운로드 기록
        FileDownloadHistory.objects.create(
            reason=validated_data.get("reason"),
            user=self.context["request"].user,
            file=instance,
        )
        return instance

    class Meta:
        model = File
        fields = [
            "reason",
            "url",
            "fields",
            "file_name",
            "extension",
        ]
        read_only_fields = [
            "file_name",
            "extension",
        ]
