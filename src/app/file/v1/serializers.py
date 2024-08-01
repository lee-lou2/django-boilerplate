from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework import serializers, exceptions
from uuid_extensions import uuid7str

from app.file.models import File, FileStatus
from app.file.utils import generate_presigned, has_file_in_s3


class FilePresignedSerializer(serializers.ModelSerializer):
    """파일 업로드 프리사인드 시리얼라이저"""

    url = serializers.URLField(read_only=True, help_text="Presigned URL Host")
    fields = serializers.JSONField(read_only=True, help_text="Presigned URL Fields")
    content_label = serializers.CharField(write_only=True, help_text="컨텐츠 종류")
    content_type = serializers.CharField(write_only=True, help_text="컨텐츠 종류")

    # content_type mapper
    CONTENT_TYPE_MAPPER = {
        # 특정 모델이 대상이 되는 경우
        # "qna": {"app_label": "qna", "model": "qna"},
        # 특정 라벨이 대상이 대는 경우
        "notice": None,
    }

    def to_internal_value(self, data):
        file_id = uuid7str()
        data["file_id"] = file_id
        now = timezone.localtime()
        file_name = data.get("file_name")
        if file_name and "." in file_name:
            ext = file_name.split(".")[-1]
            content_label = data.get("content_label")
            data["content_type"] = content_label
            object_key = (
                f"{content_label}/{now.year}/{now.month}/{now.day}/{file_id}.{ext}"
            )
            data["object_key"] = object_key
        return super().to_internal_value(data)

    def validate_content_label(self, attr):
        # 미리 지정된 타입에 존재 여부 확인
        if attr not in self.CONTENT_TYPE_MAPPER.keys():
            raise exceptions.ValidationError("Invalid content type")
        return attr

    def validate_content_type(self, attr):
        # 컨텐츠 종류 존재 여부 확인
        content_type_values = self.CONTENT_TYPE_MAPPER.get(attr)
        if not content_type_values:
            return None
        if not isinstance(content_type_values, dict):
            raise exceptions.ValidationError("Invalid content type")
        # ContentType 객체 반환
        obj = ContentType.objects.filter(**content_type_values).first()
        if not obj:
            raise exceptions.ValidationError("Invalid content type")
        return obj

    def to_representation(self, instance):
        resp = super().to_representation(instance)
        url, fields = generate_presigned(instance.object_key)
        resp.update(url=url)
        resp.update(fields=fields)
        return resp

    class Meta:
        model = File
        fields = [
            "file_id",
            "file_name",
            "file_size",
            "content_label",
            "content_type",
            "object_key",
            "user",
            "url",
            "fields",
        ]
        extra_kwargs = {
            "file_name": {"write_only": True},
            "file_size": {"write_only": True},
            "object_key": {"write_only": True},
            "user": {"write_only": True},
        }


class FileSerializer(serializers.ModelSerializer):
    status = serializers.IntegerField(help_text="파일 상태", default=FileStatus.DONE)
    file_url = serializers.SerializerMethodField(help_text="파일 URL")

    def validate(self, attrs):
        # 파일이 S3에 존재하는지 확인
        if not has_file_in_s3(self.instance.object_key):
            raise exceptions.ValidationError("Invalid file id")
        return attrs

    def get_file_url(self, instance):
        cloud_front_url = settings.AWS_CLOUDFRONT_URL
        return f"{cloud_front_url}{instance.object_key}"

    class Meta:
        model = File
        fields = [
            "file_id",
            "file_name",
            "file_size",
            "content_label",
            "status",
            "file_url",
        ]
        read_only_fields = [
            "file_id",
            "file_name",
            "file_size",
            "content_label",
        ]
