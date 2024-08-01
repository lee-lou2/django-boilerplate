from django.core.validators import MinLengthValidator, validate_integer
from django.db import models

from app.common.models import BaseModel


class EmailVerifier(BaseModel):
    email = models.EmailField(verbose_name="이메일")
    code = models.CharField(verbose_name="인증번호", max_length=6)
    token = models.CharField(verbose_name="토큰", max_length=40)
    is_verified = models.BooleanField(verbose_name="인증여부", default=False)

    class Meta:
        db_table = "email_verifier"
        ordering = ["-created_at"]


class PhoneVerifier(BaseModel):
    phone = models.CharField(
        verbose_name="휴대폰번호",
        max_length=11,
        validators=[validate_integer, MinLengthValidator(10)],
    )
    code = models.CharField(verbose_name="인증번호", max_length=6)
    token = models.CharField(verbose_name="토큰", max_length=40)
    is_verified = models.BooleanField(verbose_name="인증여부", default=False)

    class Meta:
        db_table = "phone_verifier"
        ordering = ["-created_at"]
