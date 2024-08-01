from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.core.validators import MinLengthValidator, validate_integer
from django.db import models
from django.utils import timezone

from app.common.models import BaseModel, BaseModelMixin
from app.device.models import Device


class UserManager(DjangoUserManager):
    def _create_user(self, email, password, **extra_fields):
        email = User.normalize_username(email)
        user = User(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class BaseUser(BaseModelMixin, AbstractUser):
    first_name = None
    last_name = None
    username = None
    email = models.EmailField(verbose_name="이메일", unique=True)
    phone = models.CharField(
        verbose_name="휴대폰",
        max_length=11,
        blank=True,
        default="",
        validators=[validate_integer, MinLengthValidator(10)],
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # 빈값 유지
    VERIFY_FIELDS = ["email"]  # 회원가입 시 검증 받을 필드 (email, phone)
    REGISTER_FIELDS = [
        "email",
        "phone",
        "password",
    ]  # 회원가입 시 입력 받을 필드 (email, phone, password)

    is_staff = models.BooleanField(verbose_name="스태프", default=False)
    is_superuser = models.BooleanField(verbose_name="슈퍼유저여부", default=False)
    is_active = models.BooleanField(verbose_name="활성화여부", default=True)
    date_joined = models.DateTimeField(verbose_name="가입일", default=timezone.now)

    objects = UserManager()

    class Meta:
        abstract = True


class User(BaseUser):
    class Meta:
        db_table = "user"
        verbose_name = "유저"
        verbose_name_plural = verbose_name

    def connect_device(self, uid, token):
        Device.objects.update_or_create(
            uid=uid, defaults={"user": self, "token": token}
        )

    def disconnect_device(self, uid):
        self.device_set.filter(uid=uid).delete()


class SocialKindChoices(models.TextChoices):
    KAKAO = "kakao", "카카오"
    NAVER = "naver", "네이버"
    FACEBOOK = "facebook", "페이스북"
    GOOGLE = "google", "구글"
    APPLE = "apple", "애플"


class Social(BaseModel):
    user = models.OneToOneField("user.User", on_delete=models.CASCADE)
    kind = models.CharField(
        verbose_name="타입", max_length=16, choices=SocialKindChoices.choices
    )

    class Meta:
        verbose_name = "소셜"
        verbose_name_plural = verbose_name
