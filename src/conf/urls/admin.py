from django.contrib import admin
from django.urls import path

from apps.user.forms import OTPAuthenticationForm
from apps.user.v1 import views as user_views

admin.site.login_form = OTPAuthenticationForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("setup-otp/<uidb64>/<token>/", user_views.setup_otp_view, name="setup_otp"),
]
