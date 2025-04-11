from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import serializers

from apps.game.models import AttendanceCheck


class AttendanceCheckSerializer(serializers.ModelSerializer):
    """
    출석 체크 시리얼라이저:
    마지막 출석 체크 이력을 조회해서 현재의 상태를 확인
    그리고 연속 참여 여부를 확인해서 포인트를 지급
    """

    consecutive_days = serializers.IntegerField(
        help_text="연속 일수", required=False, default=0
    )

    def to_internal_value(self, data):
        # self.instance 의 check_in_date 가 어제가 아니면 0 으로 초기화
        # [Why]
        # Q. 왜 어제 체크인 날짜가 아닌 경우 0으로 초기화 하는가?
        # A. 어제 체크인 날짜가 아닌 경우, 연속 출석이라고 할 수 없음
        #    출석 체크는 하루에 한 번만 가능
        data["consecutive_days"] = 0
        if (
            self.instance
            and self.instance.check_in_date == timezone.now().date() - timedelta(days=1)
            and self.instance.consecutive_days
            < len(settings.ATTENDANCE_CHECK_REWARD_POINTS) - 1
        ):
            # 어제 출석체크 한 경우 연속 일수를 1 증가
            data["consecutive_days"] = self.instance.consecutive_days + 1
        return super().to_internal_value(data)

    def save(self, **kwargs):
        try:
            # 오늘 출석 체크 이력을 생성하거나 존재한다면 조회
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
