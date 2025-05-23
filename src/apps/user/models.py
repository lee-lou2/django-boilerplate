from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from uuid_extensions import uuid7

from common.fields.encrypt import EncryptedCharField


class UserManager(BaseUserManager):
    """User Manager"""

    def create_user(self, email, password=None, **extra_fields) -> "User":
        """Create basic user"""
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

        if extra_fields.get("is_staff") is not True:
            raise ValueError("required is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("required is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """User"""

    uuid = models.UUIDField(
        default=uuid7,
        unique=True,
        editable=False,
        verbose_name="UUID",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    agreements = models.ManyToManyField(
        "agreement.Agreement",
        through="agreement.UserAgreement",
        related_name="users",
        verbose_name="Agreement Consent",
        blank=True,
        help_text="Agreements the user has consented to",
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Email Verified",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Is Staff",
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date Joined",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"


class SocialUser(models.Model):
    """Social User"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="social_users",
        verbose_name="User",
    )
    provider = models.CharField(
        max_length=20,
        verbose_name="Social Provider",
    )
    social_id = models.CharField(
        max_length=100,
        verbose_name="Social ID",
    )
    user_data = EncryptedCharField(
        max_length=1000,
        verbose_name="Social User Data",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "social_user"
        verbose_name = "Social User"
        verbose_name_plural = "Social Users"
        unique_together = ["user", "provider"]


class UserProfile(models.Model):
    """User Profile"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="User",
    )
    nickname = models.CharField(
        unique=True,
        max_length=30,
        verbose_name="Nickname",
    )
    image = models.URLField(
        verbose_name="Profile Image",
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "user_profile"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# TODO: Need to implement identity verification logic
class UserVerification(models.Model):
    """User Identity Verification Information"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="verification",
        verbose_name="User",
    )
    name = EncryptedCharField(
        max_length=30,
        verbose_name="Encrypted Name",
    )
    phone = EncryptedCharField(
        max_length=30,
        verbose_name="Encrypted Phone Number",
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
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "user_verification"
        verbose_name = "User Identity Verification Information"
        verbose_name_plural = "User Identity Verification Information"


class UserPreference(models.Model):
    """User Preference Information"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="preference",
        verbose_name="User",
    )
    is_night_notification = models.BooleanField(
        default=False,
        verbose_name="Night Notification Consent",
    )
    is_push_notification = models.BooleanField(
        default=True,
        verbose_name="Push Notification Consent",
    )
    is_email_notification = models.BooleanField(
        default=True,
        verbose_name="Email Notification Consent",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "user_preference"
        verbose_name = "User Preference Information"
        verbose_name_plural = "User Preference Information"
