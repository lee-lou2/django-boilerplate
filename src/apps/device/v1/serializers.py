from rest_framework import serializers

from apps.device.models import Device, PushToken
from common.enums.errors import (
    E007_DEVICE_UUID_REQUIRED,
    E007_DEVICE_ALREADY_REGISTERED,
    E007_PUSH_TOKEN_REQUIRED,
    E007_PUSH_TOKEN_ALREADY_REGISTERED,
)


class DeviceSerializer(serializers.ModelSerializer):
    """
    디바이스 시리얼라이저:
    디바이스 UUID 존재 여부 확인 및 생성
    """

    def validate_uuid(self, attr):
        """UUID 유효성 검사"""
        if not attr:
            raise serializers.ValidationError(E007_DEVICE_UUID_REQUIRED)
        elif Device.objects.filter(
            uuid=attr,
            user=self.context["request"].user,
        ).exists():
            raise serializers.ValidationError(E007_DEVICE_ALREADY_REGISTERED)
        return attr

    def create(self, validated_data):
        instance = super().create(validated_data)
        # TODO: AWS SNS 의 구독 정보 업데이트
        return instance

    class Meta:
        model = Device
        fields = [
            "id",
            "uuid",
            "platform",
            "created_at",
            "updated_at",
        ]


class PushTokenSerializer(serializers.ModelSerializer):
    """
    푸시 토큰 시리얼라이저:
    사용자별 토큰 고유 여부 확인 후 등록
    추후 AWS SNS Token 등록하여 푸시 활용
    """

    def validate_token(self, attr):
        """토큰 유효성 검사"""
        if not attr:
            raise serializers.ValidationError(E007_PUSH_TOKEN_REQUIRED)
        elif PushToken.objects.filter(
            token=attr,
            device__user=self.context["request"].user,
        ).exists():
            raise serializers.ValidationError(E007_PUSH_TOKEN_ALREADY_REGISTERED)
        return attr

    def create(self, validated_data):
        """생성"""
        instance = super().create(validated_data)
        # TODO: 푸시 토큰 생성 후 endpoint arn 생성
        return instance

    class Meta:
        model = PushToken
        fields = [
            "id",
            "token",
        ]
