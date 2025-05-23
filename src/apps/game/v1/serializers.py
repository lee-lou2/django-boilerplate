from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import serializers

from apps.game.models import AttendanceCheck


class AttendanceCheckSerializer(serializers.ModelSerializer):
    """
    Attendance Check Serializer:
    Retrieves the last attendance check history to determine the current status.
    Awards points based on consecutive participation.
    """

    consecutive_days = serializers.IntegerField(
        help_text="Consecutive days", required=False, default=0
    )

    def to_internal_value(self, data):
        # If self.instance's check_in_date is not yesterday, reset to 0
        # [Why]
        # Q. Why reset to 0 if not checked in yesterday?
        # A. If not checked in yesterday, it cannot be considered consecutive attendance.
        #    Attendance check is only allowed once per day.
        data["consecutive_days"] = 0
        if (
            self.instance
            and self.instance.check_in_date == timezone.now().date() - timedelta(days=1)
            and self.instance.consecutive_days
            < len(settings.ATTENDANCE_CHECK_REWARD_POINTS) - 1
        ):
            # If checked in yesterday, increment consecutive days by 1
            data["consecutive_days"] = self.instance.consecutive_days + 1
        return super().to_internal_value(data)

    def save(self, **kwargs):
        try:
            # Create or retrieve today's attendance check history if it exists
            user = self.context["request"].user
            self.instance, _ = AttendanceCheck.objects.get_or_create(
                user=user,
                check_in_date=timezone.now().date(),
                defaults={
                    "consecutive_days": self.validated_data.get("consecutive_days")
                },
            )
        except IntegrityError:
            raise serializers.ValidationError("Attendance check already exists")
        return self.instance

    class Meta:
        model = AttendanceCheck
        fields = [
            "id",
            "check_in_date",
            "consecutive_days",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "check_in_date",
            "created_at",
        ]
