from django.db import models


class ShortUrl(models.Model):
    """단축 URL"""

    random_key = models.CharField(
        max_length=4,
        verbose_name="랜덤 키",
    )
    ios_deep_link = models.CharField(
        max_length=255,
        verbose_name="iOS 딥링크",
        null=True,
        blank=True,
    )
    ios_fallback_url = models.URLField(
        verbose_name="iOS 폴백 URL",
        null=True,
        blank=True,
    )
    android_deep_link = models.CharField(
        max_length=255,
        verbose_name="안드로이드 딥링크",
        null=True,
        blank=True,
    )
    android_fallback_url = models.URLField(
        verbose_name="안드로이드 폴백 URL",
        null=True,
        blank=True,
    )
    default_fallback_url = models.URLField(
        verbose_name="기본 폴백 URL",
    )
    hashed_value = models.CharField(
        max_length=64,
        verbose_name="해시값",
        db_index=True,
    )
    og_tag = models.JSONField(
        null=True,
        blank=True,
        verbose_name="OG 태그",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    class Meta:
        verbose_name = "단축 URL"
        verbose_name_plural = "단축 URL"
        db_table = "short_url"


class ShortUrlVisit(models.Model):
    """단축 URL 방문"""

    short_url = models.ForeignKey(
        ShortUrl,
        on_delete=models.CASCADE,
        verbose_name="단축 URL",
    )
    referrer = models.CharField(
        max_length=255,
        verbose_name="레퍼러",
        null=True,
        blank=True,
    )
    user_agent = models.TextField(
        verbose_name="사용자 에이전트",
        null=True,
        blank=True,
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="IP 주소",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    class Meta:
        verbose_name = "단축 URL 방문"
        verbose_name_plural = "단축 URL 방문"
        db_table = "short_url_visit"
