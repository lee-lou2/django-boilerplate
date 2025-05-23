from django.db import models
from uuid_extensions import uuid7


class Feed(models.Model):
    """Feed"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feeds",
        verbose_name="Author",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
    )
    content = models.TextField(
        verbose_name="Content",
    )
    image = models.URLField(
        verbose_name="Image",
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(
        "feed.FeedTag",
        related_name="feeds",
        verbose_name="Tags",
    )
    comments_count = models.IntegerField(
        default=0,
        verbose_name="Comments Count",
    )
    likes_count = models.IntegerField(
        default=0,
        verbose_name="Likes Count",
    )
    reported_count = models.IntegerField(
        default=0,
        verbose_name="Reported Count",
    )
    published_at = models.DateTimeField(
        verbose_name="Published At",
    )
    is_displayed = models.BooleanField(
        default=True,
        verbose_name="Is Displayed",
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Is Deleted",
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
        db_table = "feed"
        verbose_name = "Feed"
        verbose_name_plural = "Feeds"


class FeedTag(models.Model):
    """Feed Tag"""

    name = models.CharField(
        max_length=50,
        verbose_name="Tag Name",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        db_table = "feed_tag"
        verbose_name = "Feed Tag"
        verbose_name_plural = "Feed Tags"


class FeedLike(models.Model):
    """Feed Like"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feed_likes",
        verbose_name="User",
    )
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
        related_name="feed_likes",
        verbose_name="Feed",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        db_table = "feed_like"
        verbose_name = "Feed Like"
        verbose_name_plural = "Feed Likes"
        unique_together = ["user", "feed"]


class FeedReportReason(models.IntegerChoices):
    """Feed Report Reason"""

    INAPPROPRIATE_CONTENT = 1, "Inappropriate Content"
    SPAM = 2, "Spam"
    HATE_SPEECH = 3, "Hate Speech"
    ETC = 4, "Other"


class FeedReport(models.Model):
    """Feed Report"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feed_reports",
        verbose_name="User",
    )
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
        related_name="feed_reports",
        verbose_name="Feed",
    )
    report_reason = models.IntegerField(
        choices=FeedReportReason.choices,
        verbose_name="Report Reason",
    )
    content = models.TextField(
        verbose_name="Content",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        db_table = "feed_report"
        verbose_name = "Feed Report"
        verbose_name_plural = "Feed Reports"
        unique_together = ["user", "feed"]


class FeedComment(models.Model):
    """Feed Comment"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feed_comments",
        verbose_name="User",
    )
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
        related_name="feed_comments",
        verbose_name="Feed",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="Parent Comment",
        null=True,
        blank=True,
    )
    content = models.TextField(
        verbose_name="Content",
    )
    likes_count = models.IntegerField(
        default=0,
        verbose_name="Likes Count",
    )
    reported_count = models.IntegerField(
        default=0,
        verbose_name="Reported Count",
    )
    reply_count = models.IntegerField(
        default=0,
        verbose_name="Reply Count",
    )
    is_displayed = models.BooleanField(
        default=True,
        verbose_name="Is Displayed",
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Is Deleted",
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
        db_table = "feed_comment"
        verbose_name = "Feed Comment"
        verbose_name_plural = "Feed Comments"


class FeedCommentLike(models.Model):
    """Feed Comment Like"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feed_comment_likes",
        verbose_name="User",
    )
    feed_comment = models.ForeignKey(
        FeedComment,
        on_delete=models.CASCADE,
        related_name="feed_comment_likes",
        verbose_name="Feed Comment",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        db_table = "feed_comment_like"
        verbose_name = "Feed Comment Like"
        verbose_name_plural = "Feed Comment Likes"
        unique_together = ["user", "feed_comment"]


class FeedCommentReport(models.Model):
    """Feed Comment Report"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feed_comment_reports",
        verbose_name="User",
    )
    feed_comment = models.ForeignKey(
        FeedComment,
        on_delete=models.CASCADE,
        related_name="feed_comment_reports",
        verbose_name="Feed Comment",
    )
    report_reason = models.IntegerField(
        choices=FeedReportReason.choices,
        verbose_name="Report Reason",
    )
    content = models.TextField(
        verbose_name="Content",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        db_table = "feed_comment_report"
        verbose_name = "Feed Comment Report"
        verbose_name_plural = "Feed Comment Reports"
        unique_together = ["user", "feed_comment"]
