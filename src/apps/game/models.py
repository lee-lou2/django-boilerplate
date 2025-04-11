from django.conf import settings
from django.db import models


class AttendanceCheck(models.Model):
    """사용자 출석 체크 이력"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="attendance_checks",
        verbose_name="사용자",
    )
    check_in_date = models.DateField(
        verbose_name="참여 일자",
        db_index=True,
    )
    consecutive_days = models.PositiveIntegerField(
        verbose_name="연속 일수",
        default=0,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            # 연속 일수에 해당하는 포인트 지급
            reward_point = settings.ATTENDANCE_CHECK_REWARD_POINTS[
                self.consecutive_days
            ]
            GamePoint.objects.create(
                user=self.user,
                point=reward_point,
                reason=PointReason.ATTENDANCE_CHECK,
            )
        return super().save(*args, **kwargs)

    class Meta:
        db_table = "attendance_check"
        verbose_name = "출석 체크 이력"
        verbose_name_plural = verbose_name
        unique_together = ["user", "check_in_date"]


class PointReason(models.IntegerChoices):
    """포인트 발급 사유"""

    ATTENDANCE_CHECK = 1, "출석 체크"
    COIN_FLIP = 2, "동전 뒤집기"


class GamePoint(models.Model):
    """게임 포인트"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="game_points",
        verbose_name="사용자",
    )
    point = models.IntegerField(
        verbose_name="포인트",
        help_text="지급/차감 포인트",
    )
    reason = models.PositiveSmallIntegerField(
        choices=PointReason.choices,
        verbose_name="사유",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    class Meta:
        db_table = "game_point"
        verbose_name = "게임 포인트"
        verbose_name_plural = verbose_name
