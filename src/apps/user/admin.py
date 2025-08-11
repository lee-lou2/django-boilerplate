from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import (
    UserChangeForm,
)
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from apps.user.forms import UserCreationForm
from apps.user.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ["uuid", "email", "is_staff", "is_verified", "is_active"]
    list_filter = ["is_staff", "is_verified", "is_active"]
    search_fields = ["email", "uuid"]
    ordering = ["-date_joined"]

    fieldsets = (
        (_("User Info"), {"fields": ["uuid", "email"]}),
        (
            _("Permissions"),
            {
                "fields": [
                    "is_active",
                    "is_verified",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ]
            },
        ),
        (_("Important dates"), {"fields": ["last_login", "date_joined"]}),
    )

    add_fieldsets = [(None, {"fields": ["email"]})]
    readonly_fields = ["uuid", "last_login", "date_joined"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            # 신규 사용자 생성 시 OTP 설정 페이지를 전송
            self.send_setup_email(request, obj)

    def send_setup_email(self, request, user):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        setup_url = request.build_absolute_uri(
            reverse("setup_otp", kwargs={"uidb64": uid, "token": token})
        )
        message = render_to_string(
            "emails/setup_account.html",
            {
                "user": user,
                "setup_url": setup_url,
            },
        )

        send_mail(
            "백오피스 계정 설정을 완료해주세요.",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
        )
