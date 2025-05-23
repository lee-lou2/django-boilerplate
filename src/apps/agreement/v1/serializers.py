from rest_framework import serializers

from apps.agreement.models import Agreement, UserAgreement, UserAgreementHistory
from common.enums.errors import (
    E009_AGREEMENT_ID_REQUIRED,
    E009_AGREEMENT_NOT_FOUND,
    E009_AGREEMENT_REQUIRED,
    E009_AGREEMENT_REQUIRED_ALL,
)


class AgreementSerializer(serializers.ModelSerializer):
    """
    Agreement List Serializer:
    Retrieves currently valid agreements.
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
    User Agreement Consent Serializer:
    Retrieves and updates the list of agreements I have agreed/disagreed to.
    """

    agreement = AgreementSerializer(read_only=True, help_text="Agreement information")

    def validate_is_agreed(self, attr):
        # For required agreements, is_agreed must be True
        if self.instance.agreement.is_required and not attr:
            raise serializers.ValidationError(E009_AGREEMENT_REQUIRED)
        return attr

    def update(self, instance, validated_data):
        before_data = {
            "is_agreed": instance.is_agreed,
            "updated_at": instance.updated_at.timestamp(),
        }
        instance = super().update(instance, validated_data)
        # Save previous record
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
    User Agreement Consent Internal Item Serializer:
    Each agreement item in the list during user registration.
    """

    id = serializers.IntegerField(help_text="Agreement ID")
    is_agreed = serializers.BooleanField(help_text="Agreement consent status")


class UserAgreementCreateSerializer(serializers.Serializer):
    """
    User Agreement Consent Serializer:
    Consents to the agreements in the list during user registration.
    """

    agreements = serializers.ListField(
        child=UserAgreementCreateItemSerializer(),
        required=True,
        write_only=True,
        help_text="User agreement consent information",
    )

    def validate_agreements(self, attrs):
        for attr in attrs:
            # 1. Check if id and is_agreed fields exist
            if "id" not in attr or "is_agreed" not in attr:
                raise serializers.ValidationError(E009_AGREEMENT_ID_REQUIRED)
            # 2. Check if the agreement exists
            agreement = Agreement.objects.filter(id=attr["id"]).first()
            if not agreement:
                raise serializers.ValidationError(E009_AGREEMENT_NOT_FOUND)
            # 3. Check if a required agreement has not been agreed to
            if agreement.is_required and not attr["is_agreed"]:
                raise serializers.ValidationError(E009_AGREEMENT_REQUIRED)
        # 4. Check if there are any active agreements not included
        if (
            Agreement.objects.filter(is_active=True)
            .exclude(id__in=[item["id"] for item in attrs])
            .exists()
        ):
            raise serializers.ValidationError(E009_AGREEMENT_REQUIRED_ALL)
        return attrs

    def create(self, validated_data):
        # Save agreement consent information
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
