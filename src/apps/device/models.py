from django.db import models


class DevicePlatform(models.IntegerChoices):
    """Device platform"""

    ANDROID = 1, "Android"
    IOS = 2, "iOS"
    WEB = 3, "Web"


class Device(models.Model):
    """Device"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="devices",
        verbose_name="User",
    )
    # [Why]
    # Q. Why is the device UUID set as unique?
    # A. Because the UUID uniquely identifies the device
    uuid = models.UUIDField(
        unique=True,
        verbose_name="UUID",
    )
    platform = models.CharField(
        max_length=50,
        choices=DevicePlatform.choices,
        default=DevicePlatform.WEB,
        verbose_name="Platform",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )

    class Meta:
        db_table = "device"
        verbose_name = "Device"
        verbose_name_plural = "Devices"


class PushToken(models.Model):
    """Push token"""

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="push_tokens",
        verbose_name="Device",
    )
    token = models.CharField(
        max_length=255,
        verbose_name="Token",
    )
    endpoint_arn = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Endpoint ARN",
    )
    is_valid = models.BooleanField(
        default=True,
        verbose_name="Is valid",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )

    def save(self, *args, **kwargs):
        # Invalidate existing tokens when a new one is added or updated as valid
        if self.is_valid:
            self.device.push_tokens.filter(is_valid=True).update(is_valid=False)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "push_token"
        verbose_name = "Push token"
        verbose_name_plural = "Push tokens"
        unique_together = ["device", "token"]
