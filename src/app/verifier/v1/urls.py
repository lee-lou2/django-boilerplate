from django.urls import path

from app.verifier.v1.views import (
    EmailVerifierConfirmView,
    EmailVerifierCreateView,
    PhoneVerifierConfirmView,
    PhoneVerifierCreateView,
)

urlpatterns = [
    path("verifier/email_verifier/", EmailVerifierCreateView.as_view()),
    path("verifier/email_verifier/confirm/", EmailVerifierConfirmView.as_view()),
    path("verifier/phone_verifier/", PhoneVerifierCreateView.as_view()),
    path("verifier/phone_verifier/confirm/", PhoneVerifierConfirmView.as_view()),
]
