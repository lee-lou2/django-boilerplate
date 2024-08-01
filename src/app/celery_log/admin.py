from django.contrib import admin

from .models import CeleryLog


@admin.register(CeleryLog)
class CeleryLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "task_id",
        "args",
        "kwargs",
        "status",
        "message",
        "process_time",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status"]
    search_fields = ["name"]

    @admin.display(description="실행 시간")
    def process_time(self, obj):
        return obj.updated_at - obj.created_at
