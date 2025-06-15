from django.db import models


class ShortUrl(models.Model):
    """Short URL"""

    random_key = models.CharField(
        max_length=4,
        verbose_name="Random Key",
    )
    ios_deep_link = models.CharField(
        max_length=255,
        verbose_name="iOS Deep Link",
        null=True,
        blank=True,
    )
    ios_fallback_url = models.URLField(
        verbose_name="iOS Fallback URL",
        null=True,
        blank=True,
    )
    android_deep_link = models.CharField(
        max_length=255,
        verbose_name="Android Deep Link",
        null=True,
        blank=True,
    )
    android_fallback_url = models.URLField(
        verbose_name="Android Fallback URL",
        null=True,
        blank=True,
    )
    default_fallback_url = models.URLField(
        verbose_name="Default Fallback URL",
    )
    hashed_value = models.CharField(
        max_length=64,
        verbose_name="Hash Value",
        db_index=True,
    )
    og_tag = models.JSONField(
        null=True,
        blank=True,
        verbose_name="OG Tag",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        verbose_name = "Short URL"
        verbose_name_plural = "Short URLs"
        db_table = "short_url"


class ShortUrlVisit(models.Model):
    """Short URL Visit"""

    short_url = models.ForeignKey(
        ShortUrl,
        on_delete=models.CASCADE,
        verbose_name="Short URL",
    )
    referrer = models.CharField(
        max_length=255,
        verbose_name="Referrer",
        null=True,
        blank=True,
    )
    user_agent = models.TextField(
        verbose_name="User Agent",
        null=True,
        blank=True,
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="IP Address",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        verbose_name = "Short URL Visit"
        verbose_name_plural = "Short URL Visits"
        db_table = "short_url_visit"
