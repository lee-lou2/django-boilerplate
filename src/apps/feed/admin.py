from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.feed.models import (
    Feed,
    FeedTag,
    FeedLike,
    FeedReport,
    FeedComment,
    FeedCommentLike,
    FeedCommentReport,
)


class FeedTagInline(admin.TabularInline):
    """피드 태그 인라인"""

    model = Feed.tags.through
    extra = 1
    verbose_name = "태그"
    verbose_name_plural = "태그 목록"


class FeedCommentInline(admin.TabularInline):
    """피드 댓글 인라인"""

    model = FeedComment
    extra = 0
    fields = [
        "uuid",
        "user",
        "content",
        "likes_count",
        "reported_count",
        "is_displayed",
        "created_at",
    ]
    readonly_fields = ["uuid", "likes_count", "reported_count", "created_at"]
    show_change_link = True
    verbose_name = "댓글"
    verbose_name_plural = "댓글 목록"
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


class FeedLikeInline(admin.TabularInline):
    """피드 좋아요 인라인"""

    model = FeedLike
    extra = 0
    readonly_fields = ["created_at"]
    verbose_name = "좋아요"
    verbose_name_plural = "좋아요 목록"
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


class FeedReportInline(admin.TabularInline):
    """피드 신고 인라인"""

    model = FeedReport
    extra = 0
    readonly_fields = ["created_at"]
    verbose_name = "신고"
    verbose_name_plural = "신고 목록"
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    """피드 어드민"""

    list_display = [
        "uuid",
        "title_truncated",
        "author",
        "published_status",
        "tags_list",
        "likes_count",
        "comments_count",
        "reported_count",
        "published_at",
        "created_at",
    ]
    list_filter = [
        "published_at",
        "is_displayed",
        "is_deleted",
        "created_at",
        "updated_at",
        "tags",
    ]
    search_fields = ["title", "content", "user__profile__nickname", "user__email"]
    readonly_fields = [
        "uuid",
        "likes_count",
        "comments_count",
        "reported_count",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        ("기본 정보", {"fields": ["uuid", "user", "title", "content", "image"]}),
        ("상태 정보", {"fields": ["published_at", "is_displayed", "is_deleted"]}),
        ("통계", {"fields": ["likes_count", "comments_count", "reported_count"]}),
        ("일자", {"fields": ["created_at", "updated_at"]}),
    ]
    inlines = [FeedTagInline, FeedCommentInline, FeedLikeInline, FeedReportInline]
    actions = ["make_displayed", "make_hidden", "mark_as_deleted"]

    def title_truncated(self, obj):
        """제목 (축약)"""
        if len(obj.title) > 30:
            return f"{obj.title[:30]}..."
        return obj.title

    title_truncated.short_description = "제목"

    def author(self, obj):
        """작성자"""
        return obj.user.profile.nickname

    author.short_description = "작성자"

    def tags_list(self, obj):
        """태그 목록"""
        return ", ".join(tag.name for tag in obj.tags.all())

    tags_list.short_description = "태그"

    def published_status(self, obj):
        """발행 상태"""
        if obj.is_deleted:
            return format_html('<span style="color: red;">삭제됨</span>')
        elif not obj.is_displayed:
            return format_html('<span style="color: orange;">숨김</span>')
        else:
            return format_html('<span style="color: green;">발행됨</span>')

    published_status.short_description = "상태"

    def make_displayed(self, request, queryset):
        """노출 처리"""
        updated = queryset.update(is_displayed=True)
        self.message_user(request, f"{updated}개의 피드가 노출 처리되었습니다.")

    make_displayed.short_description = "선택된 피드 노출 처리"

    def make_hidden(self, request, queryset):
        """숨김 처리"""
        updated = queryset.update(is_displayed=False)
        self.message_user(request, f"{updated}개의 피드가 숨김 처리되었습니다.")

    make_hidden.short_description = "선택된 피드 숨김 처리"

    def mark_as_deleted(self, request, queryset):
        """삭제 처리"""
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f"{updated}개의 피드가 삭제 처리되었습니다.")

    mark_as_deleted.short_description = "선택된 피드 삭제 처리"


@admin.register(FeedTag)
class FeedTagAdmin(admin.ModelAdmin):
    """피드 태그 어드민"""

    list_display = ["id", "name", "feeds_count", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at"]

    def feeds_count(self, obj):
        """피드 수"""
        count = obj.feeds.count()
        return count

    feeds_count.short_description = "피드 수"


class ReplyInline(admin.TabularInline):
    """대댓글 인라인"""

    model = FeedComment
    fk_name = "parent"
    extra = 0
    fields = [
        "uuid",
        "user",
        "content",
        "likes_count",
        "reported_count",
        "is_displayed",
        "created_at",
    ]
    readonly_fields = ["uuid", "likes_count", "reported_count", "created_at"]
    verbose_name = "답글"
    verbose_name_plural = "답글 목록"
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


class FeedCommentLikeInline(admin.TabularInline):
    """피드 댓글 좋아요 인라인"""

    model = FeedCommentLike
    extra = 0
    readonly_fields = ["created_at"]
    verbose_name = "좋아요"
    verbose_name_plural = "좋아요 목록"
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


class FeedCommentReportInline(admin.TabularInline):
    """피드 댓글 신고 인라인"""

    model = FeedCommentReport
    extra = 0
    readonly_fields = ["created_at"]
    verbose_name = "신고"
    verbose_name_plural = "신고 목록"
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FeedComment)
class FeedCommentAdmin(admin.ModelAdmin):
    """피드 댓글 어드민"""

    list_display = [
        "uuid",
        "feed_title",
        "author",
        "content_truncated",
        "parent_comment",
        "reply_count",
        "likes_count",
        "reported_count",
        "display_status",
        "created_at",
    ]
    list_filter = ["is_displayed", "is_deleted", "created_at", "updated_at"]
    search_fields = ["content", "user__profile__nickname", "user__email", "feed__title"]
    readonly_fields = [
        "uuid",
        "likes_count",
        "reported_count",
        "reply_count",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        ("기본 정보", {"fields": ["uuid", "user", "feed", "parent", "content"]}),
        ("상태 정보", {"fields": ["is_displayed", "is_deleted"]}),
        ("통계", {"fields": ["likes_count", "reported_count", "reply_count"]}),
        ("일자", {"fields": ["created_at", "updated_at"]}),
    ]
    raw_id_fields = ["feed", "parent"]
    inlines = [ReplyInline, FeedCommentLikeInline, FeedCommentReportInline]
    actions = ["make_displayed", "make_hidden", "mark_as_deleted"]

    def feed_title(self, obj):
        """피드 제목"""
        if len(obj.feed.title) > 20:
            return f"{obj.feed.title[:20]}..."
        return obj.feed.title

    feed_title.short_description = "피드"

    def author(self, obj):
        """작성자"""
        return obj.user.profile.nickname

    author.short_description = "작성자"

    def content_truncated(self, obj):
        """내용 (축약)"""
        if len(obj.content) > 30:
            return f"{obj.content[:30]}..."
        return obj.content

    content_truncated.short_description = "내용"

    def parent_comment(self, obj):
        """부모 댓글"""
        if obj.parent:
            content = obj.parent.content
            if len(content) > 20:
                content = f"{content[:20]}..."
            return f"↪️ {content}"
        return "-"

    parent_comment.short_description = "부모 댓글"

    def display_status(self, obj):
        """표시 상태"""
        if obj.is_deleted:
            return format_html('<span style="color: red;">삭제됨</span>')
        elif not obj.is_displayed:
            return format_html('<span style="color: orange;">숨김</span>')
        else:
            return format_html('<span style="color: green;">표시중</span>')

    display_status.short_description = "상태"

    def make_displayed(self, request, queryset):
        """노출 처리"""
        updated = queryset.update(is_displayed=True)
        self.message_user(request, f"{updated}개의 댓글이 노출 처리되었습니다.")

    make_displayed.short_description = "선택된 댓글 노출 처리"

    def make_hidden(self, request, queryset):
        """숨김 처리"""
        updated = queryset.update(is_displayed=False)
        self.message_user(request, f"{updated}개의 댓글이 숨김 처리되었습니다.")

    make_hidden.short_description = "선택된 댓글 숨김 처리"

    def mark_as_deleted(self, request, queryset):
        """삭제 처리"""
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f"{updated}개의 댓글이 삭제 처리되었습니다.")

    mark_as_deleted.short_description = "선택된 댓글 삭제 처리"


@admin.register(FeedReport)
class FeedReportAdmin(admin.ModelAdmin):
    """피드 신고 어드민"""

    list_display = [
        "id",
        "feed_title",
        "reporter",
        "get_report_reason",
        "content_preview",
        "created_at",
    ]
    list_filter = ["report_reason", "created_at"]
    search_fields = ["feed__title", "user__profile__nickname", "user__email", "content"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["feed", "user"]

    def feed_title(self, obj):
        """피드 제목"""
        return obj.feed.title

    feed_title.short_description = "피드"

    def reporter(self, obj):
        """신고자"""
        return obj.user.profile.nickname

    reporter.short_description = "신고자"

    def get_report_reason(self, obj):
        """신고 사유"""
        return obj.get_report_reason_display()

    get_report_reason.short_description = "신고 사유"

    def content_preview(self, obj):
        """내용 미리보기"""
        if obj.content:
            if len(obj.content) > 50:
                return f"{obj.content[:50]}..."
            return obj.content
        return "-"

    content_preview.short_description = "내용"


@admin.register(FeedCommentReport)
class FeedCommentReportAdmin(admin.ModelAdmin):
    """피드 댓글 신고 어드민"""

    list_display = [
        "id",
        "comment_preview",
        "reporter",
        "get_report_reason",
        "content_preview",
        "created_at",
    ]
    list_filter = ["report_reason", "created_at"]
    search_fields = [
        "feed_comment__content",
        "user__profile__nickname",
        "user__email",
        "content",
    ]
    readonly_fields = ["created_at"]
    raw_id_fields = ["feed_comment", "user"]

    def comment_preview(self, obj):
        """댓글 내용"""
        if len(obj.feed_comment.content) > 30:
            return f"{obj.feed_comment.content[:30]}..."
        return obj.feed_comment.content

    comment_preview.short_description = "댓글"

    def reporter(self, obj):
        """신고자"""
        return obj.user.profile.nickname

    reporter.short_description = "신고자"

    def get_report_reason(self, obj):
        """신고 사유"""
        return obj.get_report_reason_display()

    get_report_reason.short_description = "신고 사유"

    def content_preview(self, obj):
        """내용 미리보기"""
        if obj.content:
            if len(obj.content) > 50:
                return f"{obj.content[:50]}..."
            return obj.content
        return "-"

    content_preview.short_description = "내용"


admin.site.register(FeedLike)
admin.site.register(FeedCommentLike)
