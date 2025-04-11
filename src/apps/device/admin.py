from django.contrib import admin
from django.utils.html import format_html

from apps.device.models import Device, PushToken


class PushTokenInline(admin.TabularInline):
    """푸시 토큰 인라인"""

    model = PushToken
    extra = 0
    readonly_fields = ["created_at", "updated_at"]
    fields = ["token", "endpoint_arn", "is_valid", "created_at", "updated_at"]
    show_change_link = True


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """디바이스 어드민"""

    list_display = [
        "id",
        "uuid",
        "user_username",
        "created_at",
        "updated_at",
        "push_token_count",
    ]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["uuid", "user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["user"]
    inlines = [PushTokenInline]

    def user_username(self, obj):
        """사용자 이름"""
        return obj.user.profile.nickname

    user_username.short_description = "사용자"

    def push_token_count(self, obj):
        """유효한 푸시 토큰 수"""
        valid_count = obj.push_tokens.filter(is_valid=True).count()
        total_count = obj.push_tokens.count()

        if valid_count == 0:
            color = "red"
        else:
            color = "green"

        return format_html(
            '<span style="color: {};">{} / {}</span>', color, valid_count, total_count
        )

    push_token_count.short_description = "유효한 토큰 / 전체 토큰"


@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    """푸시 토큰 어드민"""

    list_display = [
        "id",
        "token_truncated",
        "device_uuid",
        "user_username",
        "is_valid",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_valid", "created_at", "updated_at"]
    search_fields = [
        "token",
        "device__uuid",
        "device__user__username",
        "device__user__email",
    ]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["device"]
    actions = ["mark_as_valid", "mark_as_invalid"]

    def token_truncated(self, obj):
        """토큰 (축약)"""
        if len(obj.token) > 20:
            return f"{obj.token[:20]}..."
        return obj.token

    token_truncated.short_description = "토큰"

    def device_uuid(self, obj):
        """디바이스 UUID"""
        return obj.device.uuid

    device_uuid.short_description = "디바이스 UUID"

    def user_username(self, obj):
        """사용자 이름"""
        return obj.device.user.profile.nickname

    user_username.short_description = "사용자"

    def mark_as_valid(self, request, queryset):
        """유효로 표시"""
        updated = queryset.update(is_valid=True)
        self.message_user(request, f"{updated}개의 토큰이 유효로 표시되었습니다.")

    mark_as_valid.short_description = "선택된 토큰을 유효로 표시"

    def mark_as_invalid(self, request, queryset):
        """무효로 표시"""
        updated = queryset.update(is_valid=False)
        self.message_user(request, f"{updated}개의 토큰이 무효로 표시되었습니다.")

    mark_as_invalid.short_description = "선택된 토큰을 무효로 표시"
