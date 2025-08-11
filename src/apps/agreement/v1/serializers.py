from rest_framework import serializers

from apps.agreement.models import Agreement, UserAgreement, UserAgreementHistory
from base.enums.errors import (
    E009_AGREEMENT_ID_REQUIRED,
    E009_AGREEMENT_NOT_FOUND,
    E009_AGREEMENT_REQUIRED,
    E009_AGREEMENT_REQUIRED_ALL,
)


class AgreementSerializer(serializers.ModelSerializer):
    """
    약관 리스트 시리얼라이저:
    현재 유효한 약관을 조회
    """

    class Meta:
        model = Agreement
        fields = [
            "id",
            "title",
            "content",
            "version",
            "agreement_type",
            "order",
            "is_required",
        ]


class UserAgreementSerializer(serializers.ModelSerializer):
    """
    사용자 약관 동의 시리얼라이저:
    내가 동의/미동의한 약관 리스트 조회 및 업데이트
    """

    agreement = AgreementSerializer(read_only=True, help_text="약관 정보")

    def validate_is_agreed(self, attr):
        # 필수 약관의 경우 is_agreed가 True여야 함
        if self.instance.agreement.is_required and not attr:
            raise serializers.ValidationError(E009_AGREEMENT_REQUIRED)
        return attr

    def update(self, instance, validated_data):
        before_data = {
            "is_agreed": instance.is_agreed,
            "updated_at": instance.updated_at.timestamp(),
        }
        instance = super().update(instance, validated_data)
        # 이 전 기록 저장
        UserAgreementHistory.objects.create(
            user_agreement=instance,
            data=before_data,
        )
        return instance

    class Meta:
        model = UserAgreement
        fields = ["id", "agreement", "is_agreed"]


class UserAgreementCreateItemSerializer(serializers.Serializer):
    """
    사용자 약관 동의 내부 항목 시리얼라이저:
    회원 가입 시 리스트에 있는 각 약관 항목
    """

    id = serializers.IntegerField(help_text="약관 ID")
    is_agreed = serializers.BooleanField(help_text="약관 동의 여부")


class UserAgreementCreateSerializer(serializers.Serializer):
    """
    사용자 약관 동의 시리얼라이저:
    회원 가입 시 리스트에 있는 약관들을 동의
    """

    agreements = serializers.ListField(
        child=UserAgreementCreateItemSerializer(),
        required=True,
        write_only=True,
        help_text="사용자 약관 동의 정보",
    )

    def validate_agreements(self, attrs):
        for attr in attrs:
            # 1. id, is_agreed 필드가 있는지 확인
            if "id" not in attr or "is_agreed" not in attr:
                raise serializers.ValidationError(E009_AGREEMENT_ID_REQUIRED)
            # 2. 존재하는 약관인지 확인
            agreement = Agreement.objects.filter(id=attr["id"]).first()
            if not agreement:
                raise serializers.ValidationError(E009_AGREEMENT_NOT_FOUND)
            # 3. 필수 약관인데 동의하지 않았는지 확인
            if agreement.is_required and not attr["is_agreed"]:
                raise serializers.ValidationError(E009_AGREEMENT_REQUIRED)
        # 4. 활성화된 약관 중 포함되지 않은 약관이 있는지 확인
        if (
            Agreement.objects.filter(is_active=True)
            .exclude(id__in=[item["id"] for item in attrs])
            .exists()
        ):
            raise serializers.ValidationError(E009_AGREEMENT_REQUIRED_ALL)
        return attrs

    def create(self, validated_data):
        # 약관 동의 정보 저장
        UserAgreement.objects.bulk_create(
            [
                UserAgreement(
                    user=self.context["request"].user,
                    agreement_id=item["id"],
                    is_agreed=item["is_agreed"],
                )
                for item in validated_data["agreements"]
            ]
        )
        return validated_data
