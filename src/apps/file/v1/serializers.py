from django.utils import timezone
from rest_framework import serializers

from apps.file.models import File, FileStatus, FileDownloadHistory
from apps.file.v1.utils import (
    generate_upload_presigned_url,
    generate_download_presigned_url,
)


class FileUploadSerializer(serializers.ModelSerializer):
    """
    File Upload Serializer:
    Uses presigned URLs for file uploads instead of direct uploads.
    """

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), help_text="User"
    )
    url = serializers.CharField(
        read_only=True,
        help_text="S3 Upload URL",
        allow_null=True,
    )
    fields = serializers.JSONField(
        read_only=True,
        help_text="S3 Upload Fields",
        allow_null=True,
    )

    def create(self, validated_data):
        instance = super().create(validated_data)
        # Save S3 file path
        content_type = ""
        file_name = f"{instance.uuid}.{instance.extension}"
        now = timezone.now()
        object_key = (
            f"files/{content_type}/{now.year}/{now.month}/{now.day}/{file_name}"
        )
        # Add presigned information
        # [Why]
        # Q. Why generate a presigned URL for S3 upload?
        # A. To prevent anyone from uploading any file.
        #    Presigned URLs ensure that only authorized users can upload.
        #    Also, to ensure users can only upload their own files.
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
    File Update Serializer:
    Updates status after file upload, handles delete requests.
    """

    class Meta:
        model = File
        fields = ["status"]


class FileDownloadSerializer(serializers.ModelSerializer):
    """
    File Download Serializer:
    Retrieves a list of files available for download.
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
    File Download Presigned Serializer:
    Uses presigned URLs for file downloads.
    """

    reason = serializers.CharField(
        write_only=True,
        help_text="Download reason",
    )
    url = serializers.CharField(
        read_only=True,
        help_text="S3 Download URL",
        allow_null=True,
    )
    fields = serializers.JSONField(
        read_only=True,
        help_text="S3 Download Fields",
        allow_null=True,
    )

    def update(self, instance, validated_data):
        """Generate file download presigned URL"""
        # [Why]
        # Q. Why generate a presigned URL for file download?
        # A. To prevent anyone from downloading any file.
        #    Presigned URLs ensure that only authorized users can download.
        #    Note: Files that anyone can download should be configured for download via CDN.
        response = generate_download_presigned_url(
            object_key=instance.object_key,
        )
        instance.fields = response.get("fields")
        instance.url = response.get("url")
        # Record file download
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
