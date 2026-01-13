import qrcode
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice
from uuid_extensions import uuid7

from base.fields.encrypt import EncryptedCharField


class UserManager(BaseUserManager):
    """사용자 매니저"""

    def create_user(self, email, password=None, **extra_fields) -> "User":
        """기본 사용자 생성"""
        if not email:
            raise ValueError("required email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields) -> "User":
        """Create superuser"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is False:
            raise ValueError("required is_staff=True")
        if extra_fields.get("is_superuser") is False:
            raise ValueError("required is_superuser=True")

        user = self.create_user(email, password, **extra_fields)

        # TOTP 디바이스 생성
        totp_device = TOTPDevice.objects.create(
            user=user, name=f"{user.email}_totp", confirmed=True
        )

        # QR 코드 생성 및 콘솔 출력
        # [Why]
        # Q. 왜 콘솔에 QR 코드를 출력하는가?
        # A. 어드민 페이지 로그인 시 OTP 필요
        #    슈퍼 사용자의 경우 QR 코드를 UI상으로 발급 받을 수 없기 때문
        provisioning_uri = totp_device.config_url
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # 콘솔에 QR 코드를 ASCII 아트로 출력
        print("\n" + "=" * 50)
        print(f"TOTP QR Code for superuser: {user.email}")
        print("=" * 50)
        qr.print_ascii(invert=True)
        print("=" * 50)
        print(f"Manual entry key: {totp_device.key}")
        print(f"Provisioning URI: {provisioning_uri}")
        print("=" * 50 + "\n")

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """사용자"""

    uuid = models.UUIDField(
        default=uuid7,
        unique=True,
        editable=False,
        verbose_name="UUID",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="이메일",
    )
    agreements = models.ManyToManyField(
        "agreement.Agreement",
        through="agreement.UserAgreement",
        related_name="users",
        verbose_name="약관 동의",
        blank=True,
        help_text="사용자가 동의한 약관",
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="이메일 인증 여부",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="활성화 여부",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="관리자 여부",
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="가입 일시",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "user"
        verbose_name = "사용자"
        verbose_name_plural = "사용자"

    def __str__(self):
        return self.email


class SocialUser(models.Model):
    """소셜 사용자"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="social_users",
        verbose_name="사용자",
    )
    provider = models.CharField(
        max_length=20,
        verbose_name="소셜 제공자",
    )
    social_id = models.CharField(
        max_length=100,
        verbose_name="소셜 ID",
    )
    user_data = EncryptedCharField(
        max_length=1000,
        verbose_name="소셜 사용자 데이터",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 일시",
    )

    class Meta:
        db_table = "social_user"
        verbose_name = "소셜 사용자"
        verbose_name_plural = "소셜 사용자"
        unique_together = ["user", "provider"]


class UserProfile(models.Model):
    """사용자 프로필"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="사용자",
    )
    nickname = models.CharField(
        unique=True,
        max_length=30,
        verbose_name="닉네임",
    )
    image = models.URLField(
        verbose_name="프로필 이미지",
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 일시",
    )

    class Meta:
        db_table = "user_profile"
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필"


# TODO: 본인 인증 로직 구현 필요
class UserVerification(models.Model):
    """사용자 본인 인증 정보"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="verification",
        verbose_name="사용자",
    )
    name = EncryptedCharField(
        max_length=30,
        verbose_name="암호화된 이름",
    )
    phone = EncryptedCharField(
        max_length=30,
        verbose_name="안호화된 전화번호",
    )
    ci = models.CharField(
        max_length=100,
        verbose_name="CI",
    )
    di = models.CharField(
        max_length=100,
        verbose_name="DI",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 일시",
    )

    class Meta:
        db_table = "user_verification"
        verbose_name = "사용자 본인 인증 정보"
        verbose_name_plural = "사용자 본인 인증 정보"


class UserPreference(models.Model):
    """사용자 선호 정보"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="preference",
        verbose_name="사용자",
    )
    is_night_notification = models.BooleanField(
        default=False,
        verbose_name="야간 수신 동의",
    )
    is_push_notification = models.BooleanField(
        default=True,
        verbose_name="푸시 알림 동의",
    )
    is_email_notification = models.BooleanField(
        default=True,
        verbose_name="이메일 알림 동의",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 일시",
    )

    class Meta:
        db_table = "user_preference"
        verbose_name = "사용자 선호 정보"
        verbose_name_plural = "사용자 선호 정보"
