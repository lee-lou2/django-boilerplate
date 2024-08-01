from django.contrib import admin

from app.withdrawal_user.models import WithdrawalUser


@admin.register(WithdrawalUser)
class WithdrawalUserAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "created_at"]
