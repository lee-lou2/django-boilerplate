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
    Device Serializer:
    Checks for the existence of a device UUID and creates it.
    """

    def validate_uuid(self, attr):
        """UUID validation"""
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
        # TODO: Update subscription information for AWS SNS
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
    Push Token Serializer:
    Checks for token uniqueness per user and then registers it.
    Will be used for push notifications by registering with AWS SNS Token later.
    """

    def validate_token(self, attr):
        """Token validation"""
        if not attr:
            raise serializers.ValidationError(E007_PUSH_TOKEN_REQUIRED)
        elif PushToken.objects.filter(
            token=attr,
            device__user=self.context["request"].user,
        ).exists():
            raise serializers.ValidationError(E007_PUSH_TOKEN_ALREADY_REGISTERED)
        return attr

    def create(self, validated_data):
        """Create"""
        instance = super().create(validated_data)
        # TODO: Create endpoint ARN after push token creation
        return instance

    class Meta:
        model = PushToken
        fields = [
            "id",
            "token",
        ]
