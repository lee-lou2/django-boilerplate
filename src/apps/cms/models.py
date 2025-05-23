from django.db import models
from uuid_extensions import uuid7


class Notice(models.Model):
    """Notice"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    author = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="Author",
        help_text="Notice author",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="Title",
    )
    content = models.TextField(
        verbose_name="Content",
        help_text="Content",
    )
    published_at = models.DateTimeField(
        verbose_name="Published At",
        help_text="Notice publication date and time",
        db_index=True,
    )
    # Display period
    start_at = models.DateTimeField(
        verbose_name="Start At",
        help_text="Notice start date and time",
    )
    end_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="End At",
        help_text="Notice end date and time",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Is Published",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "notice"
        verbose_name = "Notice"
        verbose_name_plural = "Notices"


class Event(models.Model):
    """Event"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    author = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="Author",
        help_text="Event author",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="Title",
    )
    content = models.TextField(
        verbose_name="Content",
        help_text="Content",
    )
    # Display period
    start_at = models.DateTimeField(
        verbose_name="Start At",
        help_text="Event start date and time",
    )
    end_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="End At",
        help_text="Event end date and time",
    )
    # Event period
    event_start_at = models.DateTimeField(
        verbose_name="Event Start At",
        help_text="Actual event start date and time",
    )
    event_end_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Event End At",
        help_text="Actual event end date and time",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Is Published",
    )
    published_at = models.DateTimeField(
        verbose_name="Published At",
        help_text="Event publication date and time",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "event"
        verbose_name = "Event"
        verbose_name_plural = "Events"


class FaqCategory(models.Model):
    """FAQ Category"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Category Name",
        help_text="Category name",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "faq_category"
        verbose_name = "FAQ Category"
        verbose_name_plural = "FAQ Categories"


class Faq(models.Model):
    """FAQ"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    author = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="Author",
        help_text="FAQ author",
    )
    category = models.ForeignKey(
        FaqCategory,
        on_delete=models.CASCADE,
        verbose_name="Category",
        help_text="FAQ category",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="Title",
    )
    content = models.TextField(
        verbose_name="Content",
        help_text="Content",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Is Published",
    )
    published_at = models.DateTimeField(
        verbose_name="Published At",
        help_text="FAQ publication date and time",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "faq"
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
