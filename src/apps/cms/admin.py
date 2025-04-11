from django.contrib import admin
from django.utils import timezone
from .models import Notice, Event, Faq


@admin.action(description="선택된 항목들을 발행 상태로 변경")
def make_published(modeladmin, request, queryset):
    queryset_to_update_published_at = queryset.filter(published_at__isnull=True)
    queryset_to_update_published_at.update(published_at=timezone.now())
    queryset.update(is_published=True)


@admin.action(description="선택된 항목들을 미발행 상태로 변경")
def make_unpublished(modeladmin, request, queryset):
    queryset.update(is_published=False)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "is_published",
        "published_at",
        "start_at",
        "end_at",
        "created_at",
    )
    list_filter = (
        "is_published",
        "author",
        "start_at",
        "end_at",
    )
    search_fields = (
        "title",
        "content",
        "author__profile__nickname",
    )
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-created_at")

    fieldsets = (
        ("기본 정보", {"fields": ("title", "author", "content")}),
        (
            "발행 및 표시 설정",
            {"fields": ("is_published", "published_at", "start_at", "end_at")},
        ),
        (
            "메타 정보 (읽기 전용)",
            {
                "fields": ("uuid", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("uuid", "created_at", "updated_at")
    actions = [make_published, make_unpublished]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "is_published",
        "published_at",
        "start_at",
        "end_at",
        "event_start_at",
        "event_end_at",
        "created_at",
    )
    list_filter = (
        "is_published",
        "author",
        "start_at",
        "event_start_at",
    )
    search_fields = (
        "title",
        "content",
        "author__profile__nickname",
    )
    date_hierarchy = "event_start_at"
    ordering = ("-event_start_at", "-created_at")

    fieldsets = (
        ("기본 정보", {"fields": ("title", "author", "content")}),
        ("이벤트 기간", {"fields": ("event_start_at", "event_end_at")}),
        (
            "발행 및 표시 설정",
            {"fields": ("is_published", "published_at", "start_at", "end_at")},
        ),
        (
            "메타 정보 (읽기 전용)",
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("uuid", "created_at", "updated_at")
    actions = [make_published, make_unpublished]


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "is_published",
        "published_at",
        "created_at",
    )
    list_filter = (
        "is_published",
        "author",
    )
    search_fields = (
        "title",
        "content",
        "author__profile__nickname",
    )
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-created_at")

    fieldsets = (
        ("기본 정보", {"fields": ("title", "author", "content")}),
        (
            "발행 설정",
            {"fields": ("is_published", "published_at")},
        ),
        (
            "메타 정보 (읽기 전용)",
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("uuid", "created_at", "updated_at")
    actions = [make_published, make_unpublished]
