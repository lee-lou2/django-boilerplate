from django.contrib import admin

from app.user.models import Device, Social, User


class DeviceInline(admin.TabularInline):
    model = Device


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ["email"]
    list_display = ["email", "date_joined", "is_active", "is_staff"]
    list_filter = ["is_staff"]
    exclude = ["last_login", "user_permissions"]
    filter_horizontal = ["groups"]

    def save_form(self, request, form, change):
        input_password = request.POST.get("password")
        instance = super().save_form(request, form, change)

        if not change:  # create
            instance.set_password(input_password)
        else:  # update
            obj = self.get_object(request, request.resolver_match.kwargs["object_id"])
            if (
                input_password and not input_password == obj.password
            ):  # input이 있고 변경되었을 때
                instance.set_password(input_password)
        instance.save()

        return instance


@admin.register(Social)
class SocialAdmin(admin.ModelAdmin):
    pass


@admin.register(Device)
class Device(admin.ModelAdmin):
    pass
