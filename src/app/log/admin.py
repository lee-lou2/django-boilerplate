from django.contrib import admin

from app.log.models import EmailLog, PushLog, SmsLog


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    pass


@admin.register(PushLog)
class PushLogAdmin(admin.ModelAdmin):
    pass


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    pass
