import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.template import loader
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers, exceptions
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from app.log.models import EmailLog
from app.user.models import Device, SocialKindChoices, User
from app.user.social_adapters import SocialAdapter
from app.user.v1.examples import login_examples
from app.user.validators import validate_password
from app.verifier.models import EmailVerifier, PhoneVerifier


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "phone"]


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["uid", "token"]
        extra_kwargs = {
            "uid": {"validators": None},
        }


@extend_schema_serializer(examples=login_examples)
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    device = DeviceSerializer(
        required=False,
        write_only=True,
        allow_null=True,
        help_text="모바일앱에서만 사용합니다.",
    )
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        user = authenticate(
            request=self.context["request"],
            email=attrs["email"],
            password=attrs["password"],
        )
        if user:
            refresh = self.get_token(user)
        else:
            raise ValidationError(
                {
                    "email": ["인증정보가 일치하지 않습니다."],
                    "password": ["인증정보가 일치하지 않습니다."],
                }
            )

        data = dict()
        data["refresh_token"] = str(refresh)
        data["access_token"] = str(refresh.access_token)
        if attrs.get("device"):
            user.connect_device(**attrs["device"])

        return data

    def create(self, validated_data):
        return validated_data


class UserLogoutSerializer(serializers.Serializer):
    uid = serializers.CharField(required=False, help_text="기기의 고유id")

    def create(self, validated_data):
        user = self.context["request"].user
        if validated_data.get("uid"):
            user.disconnect_device(validated_data["uid"])

        return {}


class UserSocialLoginSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True)
    state = serializers.ChoiceField(write_only=True, choices=SocialKindChoices.choices)

    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        social_user_id = self.get_social_user_id(attrs["code"], attrs["state"])
        social_email = f"{social_user_id}@{attrs['state']}.social"
        try:
            attrs["user"] = User.objects.get(
                email=social_email, password=make_password(None)
            )
        except User.DoesNotExist:
            social_token = jwt.encode(
                payload={
                    "email": social_email,
                    "expired_at": timezone.now().timestamp() + 10 * 60,
                },
                key=settings.SECRET_KEY,
            )
            raise exceptions.ValidationError({"social_token": [social_token]})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        refresh = RefreshToken.for_user(validated_data["user"])
        validated_data["access_token"] = refresh.access_token
        validated_data["refresh_token"] = refresh
        return validated_data

    def get_social_user_id(self, code, state):
        for adapter_class in SocialAdapter.__subclasses__():
            if adapter_class.key == state:
                origin = (
                    f"{'https' if self.context['request'].is_secure() else 'http'}://"
                    f"{self.context['request'].META['HTTP_HOST']}"
                )
                return adapter_class(code, origin).get_social_user_id()
        raise ModuleNotFoundError(f"{state.capitalize()}Adapter class")


class UserRegisterSerializer(serializers.Serializer):
    social_token = serializers.CharField(
        write_only=True, required=False, help_text="소셜 로그인 토큰"
    )
    email = serializers.CharField(write_only=True, required=False)
    email_token = serializers.CharField(
        write_only=True,
        required=False,
        help_text="email verifier를 통해 얻은 token값입니다.",
    )
    phone = serializers.CharField(write_only=True, required=False)
    phone_token = serializers.CharField(
        write_only=True,
        required=False,
        help_text="phone verifier를 통해 얻은 token값입니다.",
    )
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)

    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def get_fields(self):
        fields = super().get_fields()

        if "email" in User.VERIFY_FIELDS:
            fields["email_token"].required = True
        if "email" in User.VERIFY_FIELDS or "email" in User.REGISTER_FIELDS:
            fields["email"].required = True
        if "phone" in User.VERIFY_FIELDS:
            fields["phone_token"].required = True
        if "phone" in User.VERIFY_FIELDS or "phone" in User.REGISTER_FIELDS:
            fields["phone"].required = True
        if "password" in User.REGISTER_FIELDS:
            fields["password"].required = True
            fields["password_confirm"].required = True

        return fields

    def validate(self, attrs):
        social_token = attrs.pop("social_token", None)
        email = attrs.get("email")
        email_token = attrs.pop("email_token", None)
        phone = attrs.get("phone")
        phone_token = attrs.pop("phone_token", None)

        password = attrs.get("password")
        password_confirm = attrs.pop("password_confirm", None)

        if social_token:
            payload = jwt.decode(
                social_token,
                key=settings.SECRET_KEY,
                algorithms=settings.SIMPLE_JWT_ALGORITHM,
            )
            if payload["expired_at"] < timezone.now().timestamp():
                raise ValidationError(
                    {"social_token": ["회원가입 토큰이 만료됐습니다."]}
                )
            attrs["email"] = payload["email"]

            return attrs

        # 이메일 검증
        if (
            "email" in User.VERIFY_FIELDS
            and not EmailVerifier.objects.filter(
                email=email, token=email_token, is_verified=True
            ).exists()
        ):
            raise ValidationError("이메일 인증을 진행해주세요.")

        if (
            "email" in User.VERIFY_FIELDS or "email" in User.REGISTER_FIELDS
        ) and User.objects.filter(email=email).exists():
            raise ValidationError({"email": ["이미 가입된 이메일입니다."]})

        # 휴대폰 검증
        if "phone" in User.VERIFY_FIELDS and not PhoneVerifier.objects.exists(
            phone=phone, token=phone_token, is_verified=True
        ):
            raise ValidationError("휴대폰 인증을 진행해주세요.")

        if (
            "phone" in User.VERIFY_FIELDS or "phone" in User.REGISTER_FIELDS
        ) and User.objects.filter(phone=phone).exists():
            raise ValidationError({"phone": ["이미 가입된 휴대폰입니다."]})

        # 비밀번호 검증
        if "password" in User.REGISTER_FIELDS:
            errors = {}
            if password != password_confirm:
                errors["password"] = ["비밀번호가 일치하지 않습니다."]
                errors["password_confirm"] = ["비밀번호가 일치하지 않습니다."]
            else:
                try:
                    validate_password(password)
                except DjangoValidationError as error:
                    errors["password"] = list(error)
                    errors["password_confirm"] = list(error)
            if errors:
                raise ValidationError(errors)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        refresh = RefreshToken.for_user(user)
        return {
            "access_token": refresh.access_token,
            "refresh_token": refresh,
        }


class UserRefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
    access_token = serializers.CharField(read_only=True)
    token_class = RefreshToken

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh_token"])

        data = {"access_token": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            data["refresh_token"] = str(refresh)

        return data


class UserPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        try:
            user = User.objects.get(**validated_data)
            self.send_password_reset_email(user)
        except User.DoesNotExist:
            pass

        return validated_data

    def send_password_reset_email(self, user):
        request = self.context["request"]

        subject = "비밀번호 초기화 인증 메일"
        context = {
            "domain": settings.DOMAIN,
            "site_name": settings.SITE_NAME,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            "token": default_token_generator.make_token(user),
            "protocol": "https" if request.is_secure() else "http",
        }
        content = loader.render_to_string("password_reset_email.html", context)
        email_log = EmailLog.objects.create(
            to_set=[user.email],
            title=subject,
            content=content,
        )
        email_log.send()


class UserPasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    email = serializers.EmailField(read_only=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(attrs["uid"])))
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = AnonymousUser()
        password = attrs["password"]
        password_confirm = attrs["password_confirm"]
        token = attrs["token"]

        if not user.is_authenticated:
            raise ValidationError("존재하지 않는 유저입니다.")

        if not default_token_generator.check_token(user, token):
            raise ValidationError("이미 비밀번호를 변경하셨습니다.")

        errors = dict()
        if password != password_confirm:
            errors["password"] = ["비밀번호가 일치하지 않습니다."]
            errors["password_confirm"] = ["비밀번호가 일치하지 않습니다."]
        else:
            try:
                validate_password(password)
            except DjangoValidationError as error:
                errors["password"] = list(error)
                errors["password_confirm"] = list(error)
        if errors:
            raise ValidationError(errors)
        self.instance = user
        return attrs

    def update(self, instance, validated_data):
        password = validated_data["password"]
        instance.set_password(password)
        instance.save()
        return instance
