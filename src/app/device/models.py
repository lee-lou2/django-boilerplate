from django.db import models

from app.common.models import BaseModel


class Device(BaseModel):
    user = models.ForeignKey(
        "user.User",
        verbose_name="유저",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    uid = models.CharField(
        verbose_name="UID", max_length=64, unique=True, db_index=True
    )
    token = models.CharField(verbose_name="값", max_length=256)

    class Meta:
        db_table = "device"
        verbose_name = "디바이스"
        verbose_name_plural = verbose_name
