from django.conf import settings
from django.db import models


class AttendanceCheck(models.Model):
    """User Attendance Check History"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="attendance_checks",
        verbose_name="User",
    )
    check_in_date = models.DateField(
        verbose_name="Participation Date",
        db_index=True,
    )
    consecutive_days = models.PositiveIntegerField(
        verbose_name="Consecutive Days",
        default=0,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            # Award points corresponding to consecutive days
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
        verbose_name = "Attendance Check History"
        verbose_name_plural = "Attendance Check Histories"
        unique_together = ["user", "check_in_date"]


class PointReason(models.IntegerChoices):
    """Point Issuance Reason"""

    ATTENDANCE_CHECK = 1, "Attendance Check"
    COIN_FLIP = 2, "Coin Flip"


class GamePoint(models.Model):
    """Game Points"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="game_points",
        verbose_name="User",
    )
    point = models.IntegerField(
        verbose_name="Points",
        help_text="Awarded/Deducted Points",
    )
    reason = models.PositiveSmallIntegerField(
        choices=PointReason.choices,
        verbose_name="Reason",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        db_table = "game_point"
        verbose_name = "Game Points"
        verbose_name_plural = "Game Points"
