from django.db import models
from uuid_extensions import uuid7


class Feed(models.Model):
    """피드"""

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
        verbose_name="작성자",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="제목",
    )
    content = models.TextField(
        verbose_name="내용",
    )
    image = models.URLField(
        verbose_name="이미지",
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(
        "feed.FeedTag",
        related_name="feeds",
        verbose_name="태그",
    )
    comments_count = models.IntegerField(
        default=0,
        verbose_name="댓글 수",
    )
    likes_count = models.IntegerField(
        default=0,
        verbose_name="좋아요 수",
    )
    reported_count = models.IntegerField(
        default=0,
        verbose_name="신고된 수",
    )
    published_at = models.DateTimeField(
        verbose_name="발행 일시",
    )
    is_displayed = models.BooleanField(
        default=True,
        verbose_name="노출 여부",
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="삭제 여부",
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
        db_table = "feed"
        verbose_name = "피드"
        verbose_name_plural = "피드"


class FeedTag(models.Model):
    """피드 태그"""

    name = models.CharField(
        max_length=50,
        verbose_name="태그명",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    class Meta:
        db_table = "feed_tag"
        verbose_name = "피드 태그"
        verbose_name_plural = "피드 태그"


class FeedLike(models.Model):
    """피드 좋아요"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feed_likes",
        verbose_name="사용자",
    )
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
        related_name="feed_likes",
        verbose_name="피드",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    class Meta:
        db_table = "feed_like"
        verbose_name = "피드 좋아요"
        verbose_name_plural = "피드 좋아요"
        unique_together = ["user", "feed"]


class FeedReportReason(models.IntegerChoices):
    """피드 신고 사유"""

    INAPPROPRIATE_CONTENT = 1, "부적절한 내용"
    SPAM = 2, "스팸"
    HATE_SPEECH = 3, "혐오 발언"
    ETC = 4, "기타"


class FeedReport(models.Model):
    """피드 신고"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feed_reports",
        verbose_name="사용자",
    )
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
        related_name="feed_reports",
        verbose_name="피드",
    )
    report_reason = models.IntegerField(
        choices=FeedReportReason.choices,
        verbose_name="신고 유형",
    )
    content = models.TextField(
        verbose_name="내용",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    class Meta:
        db_table = "feed_report"
        verbose_name = "피드 신고"
        verbose_name_plural = "피드 신고"
        unique_together = ["user", "feed"]


class FeedComment(models.Model):
    """피드 댓글"""

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
        verbose_name="사용자",
    )
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
        related_name="feed_comments",
        verbose_name="피드",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="부모 댓글",
        null=True,
        blank=True,
    )
    content = models.TextField(
        verbose_name="내용",
    )
    likes_count = models.IntegerField(
        default=0,
        verbose_name="좋아요 수",
    )
    reported_count = models.IntegerField(
        default=0,
        verbose_name="신고 수",
    )
    reply_count = models.IntegerField(
        default=0,
        verbose_name="답글 수",
    )
    is_displayed = models.BooleanField(
        default=True,
        verbose_name="노출 여부",
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="삭제 여부",
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
        db_table = "feed_comment"
        verbose_name = "피드 댓글"
        verbose_name_plural = "피드 댓글"


class FeedCommentLike(models.Model):
    """피드 댓글 좋아요"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feed_comment_likes",
        verbose_name="사용자",
    )
    feed_comment = models.ForeignKey(
        FeedComment,
        on_delete=models.CASCADE,
        related_name="feed_comment_likes",
        verbose_name="피드 댓글",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    class Meta:
        db_table = "feed_comment_like"
        verbose_name = "피드 댓글 좋아요"
        verbose_name_plural = "피드 댓글 좋아요"
        unique_together = ["user", "feed_comment"]


class FeedCommentReport(models.Model):
    """피드 댓글 신고"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="feed_comment_reports",
        verbose_name="사용자",
    )
    feed_comment = models.ForeignKey(
        FeedComment,
        on_delete=models.CASCADE,
        related_name="feed_comment_reports",
        verbose_name="피드 댓글",
    )
    report_reason = models.IntegerField(
        choices=FeedReportReason.choices,
        verbose_name="신고 유형",
    )
    content = models.TextField(
        verbose_name="내용",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    class Meta:
        db_table = "feed_comment_report"
        verbose_name = "피드 댓글 신고"
        verbose_name_plural = "피드 댓글 신고"
        unique_together = ["user", "feed_comment"]
