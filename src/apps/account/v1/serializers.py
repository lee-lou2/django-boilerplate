import datetime
import logging
import re

import jwt
from django.conf import settings
from rest_framework import serializers, exceptions
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from apps.account.v1.adapters import GoogleLoginAdapter
from apps.account.v1.services import (
    send_email_verification_token,
    get_cached_email_verification_data,
    EmailTemplate,
)
from apps.user.models import User
from common.enums.errors import (
    E001_INVALID_EMAIL_FORMAT,
    E001_EMAIL_NOT_VERIFIED,
    E001_EMAIL_ALREADY_IN_USE,
    E001_INVALID_PASSWORD,
    E001_PASSWORD_MISMATCH,
    E002_INVALID_HASHED_EMAIL_FORMAT,
    E002_INVALID_VERIFICATION_TOKEN,
    E002_EMAIL_ALREADY_VERIFIED,
    E002_VERIFICATION_INFO_NOT_FOUND,
    E002_VERIFICATION_TOKEN_NOT_MATCH,
    E003_INVALID_PASSWORD,
    E003_EMAIL_NOT_VERIFIED,
    E003_REFRESH_TOKEN_FAILED,
    E003_BLACKLIST_FAILED,
    E003_USER_NOT_FOUND,
    E004_INVALID_HASHED_EMAIL_FORMAT,
    E004_INVALID_VERIFICATION_TOKEN,
    E004_VERIFICATION_INFO_NOT_FOUND,
    E004_VERIFICATION_TOKEN_NOT_MATCH,
)

logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    """
    회원 가입 시리얼라이저:
    이메일의 경우 정규식과 존재 여부 등을 파악해 유효성 검사 진행(정규식은 프론트와 맞춰야함)
    비밀번호 역시 정규식에 의한 유효성 검사 진행
    패스워드 일치 여부 확인 후 회원 가입 진행(즉시 가입되지 않고 인증 이메일로 검증되면 가입됨)
    """

    password_confirm = serializers.CharField(help_text="비밀번호 확인", write_only=True)

    def validate_email(self, value):
        """이메일 유효성 검사"""
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, value):
            raise exceptions.ValidationError(E001_INVALID_EMAIL_FORMAT)
        # 계정 존재 여부 확인
        if User.objects.filter(email=value).exists():
            # 아직 검증되지 않았는지 확인
            if not User.objects.filter(email=value).first().is_verified:
                raise exceptions.ValidationError(E001_EMAIL_NOT_VERIFIED)
            raise exceptions.ValidationError(E001_EMAIL_ALREADY_IN_USE)
        return value

    def validate_password(self, value):
        """비밀번호 유효성 검사"""
        password_regex = r"^(?=.*[a-z])(?=.*\d)[a-zA-Z0-9_-]{6,30}$"
        if not re.match(password_regex, value):
            raise exceptions.ValidationError(E001_INVALID_PASSWORD)
        return value

    def validate_password_confirm(self, value):
        """비밀번호 확인 유효성 검사"""
        if self.initial_data.get("password", "") != value:
            raise exceptions.ValidationError(E001_PASSWORD_MISMATCH)
        return value

    def create(self, validated_data):
        """사용자 생성"""
        validated_data.pop("password_confirm")
        instance = User.objects.create_user(**validated_data)
        # 이메일 인증 코드 설정
        email = validated_data.get("email")
        send_email_verification_token(email, EmailTemplate.SIGNUP)
        return instance

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm"]
        extra_kwargs = {
            # 패스워드는 결과로 반환하지 않음
            "password": {"write_only": True},
            # 인증 여부에 따라 다른 결과 반환을 위해 오버라이딩
            "email": {"validators": []},
        }


class EmailVerificationSerializer(serializers.Serializer):
    """
    이메일 인증 토큰 검사 시리얼라이저:
    회원 가입 시도간 이메일 검증을 요청한 사용자가 검증을 하는 과정
    해싱된 이메일과 토큰을 유효성 검사
    캐시에 저장된 정보와 일치하는 경우 회원 가입 완료 처리
    """

    hashed_email = serializers.CharField(help_text="해시된 이메일")
    token = serializers.CharField(help_text="인증 토큰")

    def validate_hashed_email(self, value):
        """해시된 이메일 유효성 검사"""
        # md5 유효성 검사
        if not re.match(r"^[0-9a-f]{32}$", value):
            raise exceptions.ValidationError(E002_INVALID_HASHED_EMAIL_FORMAT)
        return value

    def validate_token(self, value):
        """인증 토큰 유효성 검사"""
        if not re.match(r"^[0-9a-f]{32}$", value):
            raise exceptions.ValidationError(E002_INVALID_VERIFICATION_TOKEN)
        return value

    def validate(self, attrs):
        """이메일 인증 검사"""
        # 캐시에 저장된 정보 조회
        hashed_email = attrs.get("hashed_email")
        token = attrs.get("token")
        cached_data = get_cached_email_verification_data(hashed_email)
        if not cached_data:
            raise exceptions.ValidationError(E002_VERIFICATION_INFO_NOT_FOUND)
        # 이메일로 사용자 조회
        email = cached_data.get("email", "")
        self.instance = get_object_or_404(User, email=email)
        # 검증 여부 확인
        if self.instance.is_verified:
            raise exceptions.ValidationError(E002_EMAIL_ALREADY_VERIFIED)
        # 토큰 일치 여부 확인
        if cached_data.get("token", "") != token:
            raise exceptions.ValidationError(E002_VERIFICATION_TOKEN_NOT_MATCH)
        return attrs

    def save(self, **kwargs):
        """인증 처리"""
        self.instance.is_verified = True
        self.instance.save()
        return self.instance

    def to_representation(self, instance):
        """결과 반환"""
        return {"email": self.instance.email}


class LoginSerializer(serializers.ModelSerializer):
    """
    로그인 시리얼라이저:
    이메일과 패스워드를 확인해서 토큰 발급
    """

    access_token = serializers.CharField(help_text="액세스 토큰", read_only=True)
    refresh_token = serializers.CharField(help_text="리프레시 토큰", read_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "")
        password = attrs.get("password", "")
        self.instance = get_object_or_404(User, email=email)
        # 비밀번호 일치 여부 확인
        if not self.instance.check_password(password):
            raise exceptions.ValidationError(E003_INVALID_PASSWORD)
        # 이메일 인증 여부 확인
        if not self.instance.is_verified:
            raise exceptions.ValidationError(E003_EMAIL_NOT_VERIFIED)
        return attrs

    def to_representation(self, instance):
        refresh_token = RefreshToken.for_user(instance)
        return {
            "access_token": str(refresh_token.access_token),
            "refresh_token": str(refresh_token),
        }

    class Meta:
        model = User
        fields = ["email", "password", "access_token", "refresh_token"]
        extra_kwargs = {
            # 비밀번호는 반환되지 않음
            "password": {"write_only": True},
            # 이메일은 반환되지 않고 기본 유효성 검사 제외
            "email": {"write_only": True, "validators": []},
        }


class RefreshTokenSerializer(serializers.Serializer):
    """
    리프레시 토큰 시리얼라이저:
    리프레시 토큰을 이용해서 액세스 토큰 재발급
    """

    access_token = serializers.CharField(help_text="액세스 토큰", read_only=True)
    refresh_token = serializers.CharField(help_text="리프레시 토큰", write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None

    def validate_refresh_token(self, value):
        """리프레시 토큰 유효성 검사"""
        try:
            self.token = RefreshToken(value)
        except Exception:
            raise exceptions.ValidationError(E003_REFRESH_TOKEN_FAILED)
        if not self.token.token:
            raise exceptions.ValidationError(E003_REFRESH_TOKEN_FAILED)
        return value

    def to_representation(self, instance):
        # 토큰 재발급
        token_expires_at = datetime.datetime.fromtimestamp(self.token["exp"])
        current_time = datetime.datetime.now()
        time_until_expiry = token_expires_at - current_time
        threshold_delta = datetime.timedelta(days=1)
        result = {"access_token": str(self.token.access_token)}
        # 만료 1일 전에 새로운 토큰 발급
        if time_until_expiry <= threshold_delta:
            try:
                payload = jwt.decode(
                    str(self.token),
                    settings.SIMPLE_JWT.get("SIGNING_KEY", ""),
                    algorithms=[settings.SIMPLE_JWT.get("ALGORITHM", "HS256")],
                )
                user_id = payload.get("user_id")
                user = User.objects.get(id=user_id)
            except (jwt.InvalidTokenError, User.DoesNotExist):
                raise exceptions.ValidationError(E003_USER_NOT_FOUND)
            try:
                # 현재 토큰을 블랙리스트에 추가
                self.token.blacklist()
            except AttributeError:
                pass
            new_refresh = RefreshToken.for_user(user)
            result["refresh_token"] = str(new_refresh)
            result["access_token"] = str(new_refresh.access_token)
        return result


class LogoutSerializer(serializers.Serializer):
    """
    로그아웃 시리얼라이저:
    토큰을 블랙 리스트에 넣어 다시 사용할 수 없도록 조치
    """

    refresh_token = serializers.CharField(help_text="리프레시 토큰", write_only=True)

    def validate(self, attrs):
        # 1. 액세스 토큰 블랙리스트 처리
        request = self.context.get("request")
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        access_token_value = auth_header.split(" ")[1]
        try:
            access = AccessToken(access_token_value)
            jti = access.payload.get("jti")
            if jti:
                outstanding_token = OutstandingToken.objects.filter(jti=jti).first()
                if outstanding_token:
                    BlacklistedToken.objects.get_or_create(token=outstanding_token)
                    logger.info(
                        f"Access token (jti: {jti[:8]}...) blacklisted successfully."
                    )
                else:
                    logger.warning(f"Outstanding token not found for jti: {jti[:8]}...")
            else:
                logger.warning("Access token does not contain jti claim.")
        except TokenError as e:
            logger.warning(f"Invalid access token provided in header: {e}")
        except Exception as e:
            logger.error(f"Error processing access token during logout: {e}")

        # 2. 리프레시 토큰 블랙리스트 처리
        refresh_token_value = attrs["refresh_token"]
        try:
            refresh = RefreshToken(refresh_token_value)
            refresh.blacklist()
        except TokenError:
            logger.warning(
                f"Refresh token might be already blacklisted or invalid: {refresh_token_value[:10]}..."
            )
        except Exception as e:
            logger.error(f"Error blacklisting refresh token: {e}")
            raise exceptions.ValidationError(E003_BLACKLIST_FAILED)
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """
    비밀번호 재설정 시리얼라이저:
    비밀번호 재설정 요청 시 입력된 이메일로 재설정 링크 전송
    """

    email = serializers.EmailField(help_text="이메일")

    def validate_email(self, value):
        """이메일 유효성 검사"""
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, value):
            raise exceptions.ValidationError(E001_INVALID_EMAIL_FORMAT)
        # 계정 존재 여부 확인
        if not User.objects.filter(email=value).exists():
            raise exceptions.ValidationError(E001_EMAIL_NOT_VERIFIED)
        return value

    def save(self, **kwargs):
        pass

    def to_representation(self, instance):
        email = self.validated_data["email"]
        send_email_verification_token(email, EmailTemplate.RESET_PASSWORD)
        return self.validated_data


class PasswordChangeSerializer(serializers.ModelSerializer):
    """
    비밀번호 변경 시리얼라이즈:
    해싱된 이메일과 토큰, 변경할 패스워드 유효성 검사
    유효성 검사를 모두 통과하면 패스워드 변경
    """

    hashed_email = serializers.CharField(help_text="해시된 이메일", write_only=True)
    token = serializers.CharField(help_text="인증 토큰", write_only=True)
    password_confirm = serializers.CharField(help_text="비밀번호 확인", write_only=True)

    def validate_hashed_email(self, value):
        """해시된 이메일 유효성 검사"""
        # md5 유효성 검사
        if not re.match(r"^[0-9a-f]{32}$", value):
            raise exceptions.ValidationError(E004_INVALID_HASHED_EMAIL_FORMAT)
        return value

    def validate_token(self, value):
        """인증 토큰 유효성 검사"""
        if not re.match(r"^[0-9a-f]{32}$", value):
            raise exceptions.ValidationError(E004_INVALID_VERIFICATION_TOKEN)
        return value

    def validate_password(self, value):
        """비밀번호 유효성 검사"""
        password_regex = r"^(?=.*[a-z])(?=.*\d)[a-zA-Z0-9_-]{6,30}$"
        if not re.match(password_regex, value):
            raise exceptions.ValidationError(E001_INVALID_PASSWORD)
        return value

    def validate_password_confirm(self, value):
        """비밀번호 확인 유효성 검사"""
        if self.initial_data.get("password", "") != value:
            raise exceptions.ValidationError(E001_PASSWORD_MISMATCH)
        return value

    def validate(self, attrs):
        """이메일 인증 검사"""
        # 캐시에 저장된 정보 조회
        hashed_email = attrs.get("hashed_email")
        token = attrs.get("token")
        cached_data = get_cached_email_verification_data(hashed_email)
        if not cached_data:
            raise exceptions.ValidationError(E004_VERIFICATION_INFO_NOT_FOUND)
        # 이메일로 사용자 조회
        email = cached_data.get("email", "")
        self.instance = get_object_or_404(User, email=email)
        # 토큰 일치 여부 확인
        if cached_data.get("token", "") != token:
            raise exceptions.ValidationError(E004_VERIFICATION_TOKEN_NOT_MATCH)
        return attrs

    def update(self, instance, validated_data):
        # 패스워드 변경
        instance.set_password(validated_data["password"])
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ["hashed_email", "token", "password", "password_confirm"]


class GoogleLoginSerializer(serializers.Serializer):
    """
    구글 로그인 시리얼라이저:
    소셜 로그인 어뎁터를 이용해서 구글 로그인 진행
    회원 가입이되지 않은 경우 회원 가입도 진행
    """

    code = serializers.CharField(help_text="구글 인증 코드", write_only=True)
    state = serializers.CharField(
        help_text="구글 인증 상태", write_only=True, allow_null=True
    )
    oauth_state = serializers.CharField(
        help_text="OAuth 상태", write_only=True, allow_null=True
    )
    access_token = serializers.CharField(
        help_text="액세스 토큰", read_only=True, allow_null=True
    )
    refresh_token = serializers.CharField(
        help_text="리프레시 토큰", read_only=True, allow_null=True
    )
    status = serializers.CharField(help_text="로그인 상태", read_only=True)

    def validate_oauth_state(self, attr):
        """구글 인증 코드 유효성 검사"""
        state = self.initial_data.get("state", None)
        if not state or not attr or state != attr:
            raise exceptions.ValidationError()
        return attr

    def save(self, **kwargs):
        try:
            request = self.context.get("request")
            adapter = GoogleLoginAdapter(request)
            credentials = adapter.get_token(self.validated_data["code"])
            user_data = adapter.get_user_data(credentials)
            self.instance = adapter.process_user(user_data)
        # TODO: 오류 종류별 처리 필요
        except Exception as e:
            raise exceptions.APIException(f"Google login error: {e}")

    def to_representation(self, instance):
        # 로그인 실패 - 이메일 인증 요청
        if not self.instance.is_verified:
            send_email_verification_token(self.instance.email, EmailTemplate.SIGNUP)
            return {
                "status": "verification_required",
                "access_token": None,
                "refresh_token": None,
            }
        # 로그인 성공
        refresh = RefreshToken.for_user(self.instance)
        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "status": "success",
        }
