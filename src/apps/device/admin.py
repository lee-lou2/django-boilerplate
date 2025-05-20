from django.contrib import admin
from django.utils.html import format_html

from apps.device.models import Device, PushToken


class PushTokenInline(admin.TabularInline):
    """Push token inline"""

    model = PushToken
    extra = 0
    readonly_fields = ["created_at", "updated_at"]
    fields = ["token", "endpoint_arn", "is_valid", "created_at", "updated_at"]
    show_change_link = True


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Device admin"""

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
        """User name"""
        return obj.user.profile.nickname

    user_username.short_description = "User"

    def push_token_count(self, obj):
        """Number of valid push tokens"""
        valid_count = obj.push_tokens.filter(is_valid=True).count()
        total_count = obj.push_tokens.count()

        if valid_count == 0:
            color = "red"
        else:
            color = "green"

        return format_html(
            '<span style="color: {};">{} / {}</span>', color, valid_count, total_count
        )

    push_token_count.short_description = "Valid tokens / total tokens"


@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    """Push token admin"""

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
        """Token (truncated)"""
        if len(obj.token) > 20:
            return f"{obj.token[:20]}..."
        return obj.token

    token_truncated.short_description = "Token"

    def device_uuid(self, obj):
        """Device UUID"""
        return obj.device.uuid

    device_uuid.short_description = "Device UUID"

    def user_username(self, obj):
        """User name"""
        return obj.device.user.profile.nickname

    user_username.short_description = "User"

    def mark_as_valid(self, request, queryset):
        """Mark selected tokens as valid"""
        updated = queryset.update(is_valid=True)
        self.message_user(request, f"{updated} tokens marked as valid.")

    mark_as_valid.short_description = "Mark selected tokens as valid"

    def mark_as_invalid(self, request, queryset):
        """Mark selected tokens as invalid"""
        updated = queryset.update(is_valid=False)
        self.message_user(request, f"{updated} tokens marked as invalid.")

    mark_as_invalid.short_description = "Mark selected tokens as invalid"
