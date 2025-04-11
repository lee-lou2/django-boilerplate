from django.db import models


class DevicePlatform(models.IntegerChoices):
    """디바이스 플랫폼"""

    ANDROID = 1, "Android"
    IOS = 2, "iOS"
    WEB = 3, "Web"


class Device(models.Model):
    """디바이스"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="devices",
        verbose_name="사용자",
    )
    # [Why]
    # Q. 디바이스 UUID를 unique하게 설정한 이유는?
    # A. UUID는 디바이스를 고유하게 식별하기 위한 값이기 때문
    uuid = models.UUIDField(
        unique=True,
        verbose_name="UUID",
    )
    platform = models.CharField(
        max_length=50,
        choices=DevicePlatform.choices,
        default=DevicePlatform.WEB,
        verbose_name="플랫폼",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 일시",
    )

    class Meta:
        db_table = "device"
        verbose_name = "디바이스"
        verbose_name_plural = "디바이스"


class PushToken(models.Model):
    """푸시 토큰"""

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="push_tokens",
        verbose_name="디바이스",
    )
    token = models.CharField(
        max_length=255,
        verbose_name="토큰",
    )
    endpoint_arn = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="엔드포인트 ARN",
    )
    is_valid = models.BooleanField(
        default=True,
        verbose_name="유효 여부",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 일시",
    )

    def save(self, *args, **kwargs):
        # 신규 등록 또는 유효한 토큰 업데이트 시 기존 토큰 무효화
        if self.is_valid:
            self.device.push_tokens.filter(is_valid=True).update(is_valid=False)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "push_token"
        verbose_name = "푸시 토큰"
        verbose_name_plural = "푸시 토큰"
        unique_together = ["device", "token"]
