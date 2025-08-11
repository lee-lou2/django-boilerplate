from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_otp.forms import OTPAuthenticationForm as DefaultOTPAuthenticationForm

User = get_user_model()


class OTPAuthenticationForm(DefaultOTPAuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = _("Email")
        self.fields["otp_token"] = forms.CharField(
            label=_("OTP Token"),
            required=True,
            widget=forms.TextInput(attrs={"autocomplete": "off"}),
        )


class UserCreationForm(forms.ModelForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["email"])
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ["email"]
