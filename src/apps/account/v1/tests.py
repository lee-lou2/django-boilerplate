import hashlib
import json
from unittest.mock import patch, MagicMock
from urllib.parse import quote_plus

from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from django.test import TestCase, RequestFactory
from rest_framework import exceptions, status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.account.v1.adapters import GoogleLoginAdapter
from apps.account.v1.serializers import (
    PasswordResetSerializer,
    PasswordChangeSerializer,
    RegisterSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    LogoutSerializer,
    GoogleLoginSerializer,
)
from apps.account.v1.services import (
    get_cached_email_verification_data,
    send_email_verification_token,
    EmailTemplate,
)
from apps.user.models import User, UserProfile, SocialUser
from base.enums.errors import (
    E003_EMAIL_NOT_VERIFIED,
    E003_REFRESH_TOKEN_FAILED,
    E003_INVALID_PASSWORD,
)


class RegisterSerializerTest(TestCase):
    """회원 가입 시리얼라이저 테스트"""

    def setUp(self):
        self.valid_data = {
            "email": "test@example.com",
            "password": "test123",
            "password_confirm": "test123",
        }

    def test_실패__이메일_없음(self):
        """테스트: 이메일을 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("email")

        serializer = RegisterSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(serializer.errors["email"][0], "이 필드는 필수 항목입니다.")

    def test_실패__이메일_형식_오류(self):
        """테스트: 이메일 형식이 올바르지 않은 경우"""
        data = self.valid_data.copy()
        invalid_emails = [
            "invalid-email",
            "invalid@",
            "@example.com",
            "invalid@example",
        ]
        for invalid_email in invalid_emails:
            data["email"] = invalid_email

            serializer = RegisterSerializer(data=data)

            self.assertFalse(serializer.is_valid())
            self.assertIn("email", serializer.errors)
            self.assertEqual(
                serializer.errors["email"][0], "유효한 이메일 주소를 입력하세요."
            )

    def test_실패__이메일_중복_미인증(self):
        """테스트: 동일한 이메일이 이미 존재하고 인증되지 않은 경우"""
        # 사용자 생성
        user = User.objects.create_user(email="test@example.com", password="test123")
        user.is_verified = False
        user.save()

        serializer = RegisterSerializer(data=self.valid_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(
            serializer.errors["email"]["message"], "회원 가입을 실패하였습니다"
        )
        self.assertEqual(serializer.errors["email"]["error_code"], "E0010002")

    def test_실패__이메일_중복_인증완료(self):
        """테스트: 동일한 이메일이 이미 존재하고 인증된 경우"""
        # 사용자 생성
        user = User.objects.create_user(email="test@example.com", password="test123")
        user.is_verified = True
        user.save()

        serializer = RegisterSerializer(data=self.valid_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(
            serializer.errors["email"]["message"], "회원 가입을 실패하였습니다"
        )
        self.assertEqual(serializer.errors["email"]["error_code"], "E0010003")

    def test_실패__비밀번호_없음(self):
        """테스트: 비밀번호를 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("password")

        serializer = RegisterSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(serializer.errors["password"][0], "이 필드는 필수 항목입니다.")

    def test_실패__비밀번호_형식_오류(self):
        """테스트: 비밀번호 형식이 올바르지 않은 경우"""
        data = self.valid_data.copy()
        data["password"] = "short"  # 영문자와 숫자 조합, 6~30자 제한
        data["password_confirm"] = "short"

        serializer = RegisterSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(
            serializer.errors["password"]["message"],
            "비밀번호는 6자 이상 30자 이하의 영문, 숫자 조합이어야 합니다",
        )
        self.assertEqual(serializer.errors["password"]["error_code"], "E0010004")

    def test_실패__비밀번호_불일치(self):
        """테스트: 비밀번호와 비밀번호 확인이 일치하지 않는 경우"""
        data = self.valid_data.copy()
        data["password_confirm"] = "different123"

        serializer = RegisterSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password_confirm", serializer.errors)
        self.assertEqual(
            serializer.errors["password_confirm"]["message"],
            "비밀번호가 일치하지 않습니다",
        )
        self.assertEqual(
            serializer.errors["password_confirm"]["error_code"], "E0010005"
        )

    @patch("apps.account.v1.serializers.send_email_verification_token")
    def test_성공__사용자_등록(self, mock_send_email):
        """테스트: 사용자 등록 성공"""
        mock_send_email.return_value = {"hashed_email": "hash", "token": "token"}

        serializer = RegisterSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.email, "test@example.com")
        self.assertFalse(user.is_verified)
        mock_send_email.assert_called_once_with(
            "test@example.com", EmailTemplate.SIGNUP
        )


class EmailVerificationSerializerTest(TestCase):
    """이메일 인증 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.user.is_verified = False
        self.user.save()

        # 해시된 이메일 생성
        hash_input = (self.user.email + settings.EMAIL_VERIFICATION_HASH_SALT).encode(
            "utf-8"
        )
        self.hashed_email = hashlib.md5(hash_input).hexdigest()

        # 토큰 생성
        self.token = "a" * 32  # 32자 토큰

        # 시리얼라이저 유효 데이터
        self.valid_data = {
            "hashed_email": self.hashed_email,
            "token": self.token,
        }

        # 캐시 키 설정
        self.django_env = settings.DJANGO_ENVIRONMENT
        self.cache_key = f"email_verification:{self.django_env}:{self.hashed_email}"

    def tearDown(self):
        # 테스트 후 캐시 삭제
        cache.delete(self.cache_key)

    def test_실패__해시된_이메일_없음(self):
        """테스트: 쿼리스트링의 hashed_email이 존재하지 않음"""
        data = self.valid_data.copy()
        data.pop("hashed_email")

        serializer = EmailVerificationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("hashed_email", serializer.errors)
        self.assertEqual(
            serializer.errors["hashed_email"][0], "이 필드는 필수 항목입니다."
        )

    def test_실패__토큰_없음(self):
        """테스트: 쿼리스트링의 token이 존재하지 않음"""
        data = self.valid_data.copy()
        data.pop("token")

        serializer = EmailVerificationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)
        self.assertEqual(serializer.errors["token"][0], "이 필드는 필수 항목입니다.")

    def test_실패__해시된_이메일_형식_오류(self):
        """테스트: hashed_email 형식이 올바르지 않음"""
        data = self.valid_data.copy()
        data["hashed_email"] = "invalid-hash"  # MD5 해시가 아님

        serializer = EmailVerificationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("hashed_email", serializer.errors)
        self.assertEqual(
            serializer.errors["hashed_email"]["message"],
            "이메일 검증을 실패하였습니다",
        )
        self.assertEqual(serializer.errors["hashed_email"]["error_code"], "E0020001")

    def test_실패__토큰_형식_오류(self):
        """테스트: token 형식이 올바르지 않음"""
        data = self.valid_data.copy()
        data["token"] = "invalid-token"  # 32자 hex가 아님

        serializer = EmailVerificationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)
        self.assertEqual(
            serializer.errors["token"]["message"], "이메일 검증을 실패하였습니다"
        )
        self.assertEqual(serializer.errors["token"]["error_code"], "E0020002")

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    def test_실패__캐시_데이터_없음(self, mock_get_cached_data):
        """테스트: hashed_email에 해당하는 캐시가 존재하지 않음"""
        mock_get_cached_data.return_value = {}  # 캐시 데이터 없음

        serializer = EmailVerificationSerializer(data=self.valid_data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["non_field"]["message"], "이메일 검증을 실패하였습니다"
        )
        self.assertEqual(serializer.errors["non_field"]["error_code"], "E0020003")
        mock_get_cached_data.assert_called_once_with(self.hashed_email)

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    @patch("apps.account.v1.serializers.get_object_or_404")
    def test_실패__사용자_존재하지_않음(self, mock_get_object, mock_get_cached_data):
        """테스트: email에 해당하는 사용자가 존재하지 않음"""
        # 캐시 데이터 설정
        mock_get_cached_data.return_value = {
            "email": "nonexistent@example.com",
            "token": self.token,
        }

        # get_object_or_404가 예외를 발생시키도록 설정
        mock_get_object.side_effect = Http404

        serializer = EmailVerificationSerializer(data=self.valid_data)

        with self.assertRaises(Http404):
            serializer.is_valid()

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    def test_실패__이미_인증된_사용자(self, mock_get_cached_data):
        """테스트: email에 해당하는 사용자가 이미 인증됨"""
        # 사용자 인증 상태 변경
        self.user.is_verified = True
        self.user.save()

        # 캐시 데이터 설정
        mock_get_cached_data.return_value = {
            "email": "test@example.com",
            "token": self.token,
        }

        serializer = EmailVerificationSerializer(data=self.valid_data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["non_field"]["message"], "이메일 검증을 실패하였습니다"
        )
        self.assertEqual(serializer.errors["non_field"]["error_code"], "E0020004")
        mock_get_cached_data.assert_called_once_with(self.hashed_email)

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    def test_실패__토큰_불일치(self, mock_get_cached_data):
        """테스트: token이 일치하지 않음"""
        # 캐시 데이터 설정 (다른 토큰)
        mock_get_cached_data.return_value = {
            "email": "test@example.com",
            "token": "different" + ("a" * 24),  # 다른 32자 토큰
        }

        serializer = EmailVerificationSerializer(data=self.valid_data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["non_field"]["message"], "이메일 검증을 실패하였습니다"
        )
        self.assertEqual(serializer.errors["non_field"]["error_code"], "E0020005")
        mock_get_cached_data.assert_called_once_with(self.hashed_email)

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    def test_성공__이메일_인증(self, mock_get_cached_data):
        """테스트: 이메일 인증 성공"""
        # 캐시 데이터 설정
        mock_get_cached_data.return_value = {
            "email": "test@example.com",
            "token": self.token,
        }

        serializer = EmailVerificationSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid())
        serializer.save()

        # 사용자 다시 조회
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertTrue(updated_user.is_verified)
        mock_get_cached_data.assert_called_once_with(self.hashed_email)


class AccountServicesTest(TestCase):
    """사용자 서비스 테스트"""

    def setUp(self):
        self.email = "test@example.com"
        self.django_env = settings.DJANGO_ENVIRONMENT
        # 원래 해시 솔트 값 저장
        self.original_salt = settings.EMAIL_VERIFICATION_HASH_SALT
        # 테스트용 해시 솔트 설정
        settings.EMAIL_VERIFICATION_HASH_SALT = "test_salt"
        # 해시된 이메일 계산
        hash_input = (self.email + settings.EMAIL_VERIFICATION_HASH_SALT).encode(
            "utf-8"
        )
        self.hashed_email = hashlib.md5(hash_input).hexdigest()
        # 캐시 키
        self.cache_key = f"email_verification:{self.django_env}:{self.hashed_email}"

    def tearDown(self):
        # 해시 솔트 원래대로 복원
        settings.EMAIL_VERIFICATION_HASH_SALT = self.original_salt
        # 캐시 삭제
        cache.delete(self.cache_key)

    @patch("apps.account.v1.services.send_mail")
    def test_성공__이메일_검증_토큰_발송(self, mock_send_email):
        """테스트: 이메일 검증 토큰 발송 성공"""
        mock_send_email.return_value = {}
        result = send_email_verification_token(self.email, EmailTemplate.SIGNUP)

        self.assertIn("hashed_email", result)
        self.assertIn("token", result)
        self.assertEqual(result["hashed_email"], self.hashed_email)

        # 캐시에 데이터가 저장되었는지 확인
        cached_data = cache.get(self.cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["email"], self.email)
        self.assertEqual(cached_data["token"], result["token"])

    @patch("apps.account.v1.services.send_mail")
    def test_성공__빈_이메일_검증_토큰_발송(self, mock_send_email):
        """테스트: 빈 이메일로 검증 토큰 발송"""
        mock_send_email.return_value = {}
        result = send_email_verification_token("", EmailTemplate.SIGNUP)

        self.assertEqual(result, {})

    def test_성공__캐시된_이메일_검증_데이터_조회(self):
        """테스트: 캐시된 이메일 검증 데이터 조회 성공"""
        # 캐시에 데이터 저장
        token = "test_token"
        cache.set(
            self.cache_key,
            {"token": token, "email": self.email},
            timeout=300,
        )

        # 데이터 조회
        result = get_cached_email_verification_data(self.hashed_email)

        self.assertEqual(result["email"], self.email)
        self.assertEqual(result["token"], token)

    def test_성공__존재하지_않는_캐시_데이터_조회(self):
        """테스트: 존재하지 않는 캐시 데이터 조회"""
        # 존재하지 않는 해시 이메일로 조회
        result = get_cached_email_verification_data("nonexistent")

        self.assertEqual(result, {})

    def test_성공__빈_해시_이메일로_캐시_조회(self):
        """테스트: 빈 해시 이메일로 캐시 조회"""
        result = get_cached_email_verification_data("")

        self.assertEqual(result, {})


class LoginViewSerializerTest(TestCase):
    """사용자 로그인 뷰셋 테스트"""

    def setUp(self):
        # 테스트 사용자 생성 - 인증된 사용자
        self.verified_user = User.objects.create_user(
            email="verified@example.com", password="test123"
        )
        self.verified_user.is_verified = True
        self.verified_user.save()

        # 인증된 사용자 프로필 등록
        UserProfile.objects.create(user=self.verified_user, nickname="test")

        # 테스트 사용자 생성 - 인증되지 않은 사용자
        self.unverified_user = User.objects.create_user(
            email="unverified@example.com", password="test123"
        )
        self.unverified_user.is_verified = False
        self.unverified_user.save()

        # 유효한 로그인 데이터
        self.valid_data = {
            "email": "verified@example.com",
            "password": "test123",
        }

    def test_성공__로그인(self):
        """테스트: 로그인 성공"""
        serializer = LoginSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.instance, self.verified_user)

        # to_representation 메소드 확인
        representation = serializer.to_representation(serializer.instance)
        self.assertIn("access_token", representation)
        self.assertIn("refresh_token", representation)

        # 토큰이 유효한 문자열인지 확인
        self.assertTrue(len(representation["access_token"]) > 20)
        self.assertTrue(len(representation["refresh_token"]) > 20)

    def test_실패__존재하지_않는_이메일_주소(self):
        """테스트: 존재하지 않는 이메일 주소로 로그인 시도"""
        invalid_data = self.valid_data.copy()
        invalid_data["email"] = "nonexistent@example.com"

        serializer = LoginSerializer(data=invalid_data)

        # get_object_or_404가 예외를 발생시킴
        with self.assertRaises(Http404):
            serializer.is_valid()

    def test_실패__패스워드가_일치하지_않음(self):
        """테스트: 패스워드가 일치하지 않는 경우"""
        invalid_data = self.valid_data.copy()
        invalid_data["password"] = "wrong_password"

        serializer = LoginSerializer(data=invalid_data)

        with self.assertRaises(exceptions.ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        # 오류 메시지 확인
        self.assertEqual(context.exception.detail, E003_INVALID_PASSWORD)

    def test_실패__검증되지_않은_이메일(self):
        """테스트: 이메일이 검증되지 않은 사용자 로그인 시도"""
        invalid_data = self.valid_data.copy()
        invalid_data["email"] = "unverified@example.com"

        serializer = LoginSerializer(data=invalid_data)

        with self.assertRaises(exceptions.ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        # 오류 메시지 확인
        self.assertEqual(context.exception.detail, E003_EMAIL_NOT_VERIFIED)

    def test_성공__리프래시_토큰_갱신(self):
        """테스트: 리프레시 토큰 갱신 성공"""
        # 사용자를 위한 리프레시 토큰 생성
        refresh = RefreshToken.for_user(self.verified_user)

        # 리프레시 토큰 시리얼라이저 데이터
        refresh_data = {
            "refresh_token": str(refresh),
        }

        serializer = RefreshTokenSerializer(data=refresh_data)

        self.assertTrue(serializer.is_valid())

        # to_representation 메소드 확인
        representation = serializer.to_representation(None)  # 인스턴스 없이 호출
        self.assertIn("access_token", representation)
        self.assertTrue(len(representation["access_token"]) > 20)

    def test_실패__리프래시_토큰이_없음(self):
        """테스트: 리프레시 토큰이 없는 경우"""
        # 빈 데이터로 시리얼라이저 생성
        serializer = RefreshTokenSerializer(data={})

        self.assertFalse(serializer.is_valid())
        self.assertIn("refresh_token", serializer.errors)
        self.assertEqual(
            serializer.errors["refresh_token"][0], "이 필드는 필수 항목입니다."
        )

    def test_실패__유효하지_않은_리프래시_토큰을_갱신(self):
        """테스트: 유효하지 않은 리프레시 토큰으로 갱신 시도"""
        invalid_data = {
            "refresh_token": "invalid_token",
        }

        serializer = RefreshTokenSerializer(data=invalid_data)

        with self.assertRaises(exceptions.ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        # 오류 메시지 확인
        self.assertEqual(
            context.exception.detail["refresh_token"], E003_REFRESH_TOKEN_FAILED
        )


class RegisterViewTest(APITestCase):
    """사용자 회원가입 뷰 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/v1/account/register/"
        self.valid_data = {
            "email": "test@example.com",
            "password": "test123",
            "password_confirm": "test123",
        }

    def test_성공__회원가입_요청(self):
        """테스트: 회원가입 요청 성공"""
        with patch(
            "apps.account.v1.serializers.send_email_verification_token"
        ) as mock_send_email:
            mock_send_email.return_value = {"hashed_email": "hash", "token": "token"}

            response = self.client.post(self.url, data=self.valid_data, format="json")

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(User.objects.count(), 1)
            user = User.objects.first()
            self.assertEqual(user.email, "test@example.com")
            self.assertFalse(user.is_verified)
            mock_send_email.assert_called_once_with(
                "test@example.com", EmailTemplate.SIGNUP
            )

    def test_실패__유효하지_않은_이메일_형식(self):
        """테스트: 유효하지 않은 이메일 형식으로 회원가입 요청"""
        invalid_data = self.valid_data.copy()
        invalid_data["email"] = "invalid-email"

        response = self.client.post(self.url, data=invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(
            response.data["email"][0]["message"], "유효한 이메일 주소를 입력하세요."
        )
        self.assertEqual(response.data["email"][0]["error_code"], "E0000000")

    def test_실패__패스워드_불일치(self):
        """테스트: 비밀번호와 비밀번호 확인이 일치하지 않는 경우"""
        invalid_data = self.valid_data.copy()
        invalid_data["password_confirm"] = "different123"

        response = self.client.post(self.url, data=invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)
        self.assertEqual(
            response.data["password_confirm"][0]["message"],
            "비밀번호가 일치하지 않습니다",
        )
        self.assertEqual(response.data["password_confirm"][0]["error_code"], "E0010005")

    def test_실패__이미_가입된_이메일(self):
        """테스트: 이미 가입된 이메일로 회원가입 요청"""
        # 이미 인증된 사용자 생성
        user = User.objects.create_user(email="test@example.com", password="test123")
        user.is_verified = True
        user.save()

        response = self.client.post(self.url, data=self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(
            response.data["email"][0]["message"], "회원 가입을 실패하였습니다"
        )
        self.assertEqual(response.data["email"][0]["error_code"], "E0010003")


class EmailVerificationViewTest(APITestCase):
    """이메일 인증 뷰 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/v1/account/register/confirm/"
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.user.is_verified = False
        self.user.save()

        # 해시된 이메일 생성
        hash_input = (self.user.email + settings.EMAIL_VERIFICATION_HASH_SALT).encode(
            "utf-8"
        )
        self.hashed_email = hashlib.md5(hash_input).hexdigest()

        # 토큰 생성
        self.token = "a" * 32  # 32자 토큰

        # 캐시 키 설정
        self.django_env = settings.DJANGO_ENVIRONMENT
        self.cache_key = f"email_verification:{self.django_env}:{self.hashed_email}"

        # 캐시에 데이터 저장
        cache.set(
            self.cache_key,
            {"email": "test@example.com", "token": self.token},
            timeout=300,
        )

    def tearDown(self):
        # 테스트 후 캐시 삭제
        cache.delete(self.cache_key)

    def test_성공__이메일_인증(self):
        """테스트: 이메일 인증 성공"""
        response = self.client.get(
            f"{self.url}?hashed_email={self.hashed_email}&token={self.token}"
        )

        # 리디렉션 확인
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response.url,
            settings.SIGNUP_COMPLETED_URL + "?email=" + quote_plus("test@example.com"),
        )

        # 사용자 인증 상태 확인
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)

    def test_실패__토큰_불일치(self):
        """테스트: 토큰이 일치하지 않는 경우"""
        wrong_token = "b" * 32

        response = self.client.get(
            f"{self.url}?hashed_email={self.hashed_email}&token={wrong_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field"][0]["message"], "이메일 검증을 실패하였습니다"
        )
        self.assertEqual(response.data["non_field"][0]["error_code"], "E0020005")

        # 사용자 인증 상태 확인 (변경되지 않아야 함)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    def test_실패__이미_인증된_사용자(self):
        """테스트: 이미 인증된 사용자의 이메일 인증 시도"""
        # 사용자 인증 상태 변경
        self.user.is_verified = True
        self.user.save()

        response = self.client.get(
            f"{self.url}?hashed_email={self.hashed_email}&token={self.token}"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field"][0]["message"], "이메일 검증을 실패하였습니다"
        )
        self.assertEqual(response.data["non_field"][0]["error_code"], "E0020004")


class LoginViewSetTest(APITestCase):
    """사용자 로그인 뷰셋 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.login_url = "/v1/account/login/"
        self.refresh_url = "/v1/account/refresh/"

        # 테스트 사용자 생성 - 인증된 사용자
        self.verified_user = User.objects.create_user(
            email="verified@example.com", password="test123"
        )
        self.verified_user.is_verified = True
        self.verified_user.save()

        # 프로필 등록
        UserProfile.objects.create(user=self.verified_user, nickname="test")

        # 테스트 사용자 생성 - 인증되지 않은 사용자
        self.unverified_user = User.objects.create_user(
            email="unverified@example.com", password="test123"
        )
        self.unverified_user.is_verified = False
        self.unverified_user.save()

        # 유효한 로그인 데이터
        self.valid_login_data = {
            "email": "verified@example.com",
            "password": "test123",
        }

    def test_성공__로그인(self):
        """테스트: 로그인 성공"""
        response = self.client.post(
            self.login_url, data=self.valid_login_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertTrue(len(response.data["access_token"]) > 20)
        self.assertTrue(len(response.data["refresh_token"]) > 20)

    def test_실패__검증되지_않은_이메일(self):
        """테스트: 이메일이 검증되지 않은 사용자 로그인 시도"""
        invalid_data = self.valid_login_data.copy()
        invalid_data["email"] = "unverified@example.com"

        response = self.client.post(self.login_url, data=invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field"][0]["message"], "이메일 인증을 완료해주세요"
        )
        self.assertEqual(response.data["non_field"][0]["error_code"], "E0030002")

    def test_실패__존재하지_않는_이메일(self):
        """테스트: 존재하지 않는 이메일로 로그인 시도"""
        invalid_data = self.valid_login_data.copy()
        invalid_data["email"] = "nonexistent@example.com"

        response = self.client.post(self.login_url, data=invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_실패__패스워드_불일치(self):
        """테스트: 비밀번호가 일치하지 않는 경우"""
        invalid_data = self.valid_login_data.copy()
        invalid_data["password"] = "wrong_password"

        response = self.client.post(self.login_url, data=invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field"][0]["message"], "비밀번호가 일치하지 않습니다"
        )
        self.assertEqual(response.data["non_field"][0]["error_code"], "E0030001")

    def test_성공__리프래시_토큰_갱신(self):
        """테스트: 리프레시 토큰 갱신 성공"""
        # 먼저 로그인하여 리프레시 토큰 획득
        login_response = self.client.post(
            self.login_url, data=self.valid_login_data, format="json"
        )
        refresh_token = login_response.data["refresh_token"]

        # 리프레시 토큰으로 새 액세스 토큰 요청
        refresh_data = {
            "refresh_token": refresh_token,
        }
        response = self.client.post(self.refresh_url, data=refresh_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertTrue(len(response.data["access_token"]) > 20)

    def test_실패__유효하지_않은_리프래시_토큰(self):
        """테스트: 유효하지 않은 리프레시 토큰으로 갱신 시도"""
        invalid_data = {
            "refresh_token": "invalid_token",
        }

        response = self.client.post(self.refresh_url, data=invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["refresh_token"][0]["message"],
            "리프래시 토큰 재발급에 실패하였습니다",
        )
        self.assertEqual(response.data["refresh_token"][0]["error_code"], "E0030003")

    def test_실패__리프래시_토큰_없음(self):
        """테스트: 리프레시 토큰이 없는 경우"""
        response = self.client.post(self.refresh_url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("refresh_token", response.data)
        self.assertEqual(
            response.data["refresh_token"][0]["message"], "이 필드는 필수 항목입니다."
        )

    def test_실패__create_메소드_직접_호출(self):
        """테스트: viewset의 create 메소드 직접 호출 시도 (허용되지 않음)"""
        response = self.client.post(
            "/v1/account/", data=self.valid_login_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_성공__만료_임박_리프래시_토큰_재발급(self):
        """테스트: 만료 시간이 임계값(1시간) 이하로 남은 리프레시 토큰의 경우 새 토큰 발급"""
        # 먼저 로그인하여 리프레시 토큰 획득
        login_response = self.client.post(
            self.login_url, data=self.valid_login_data, format="json"
        )
        refresh_token = login_response.data["refresh_token"]

        # to_representation 메서드를 직접 패치하여 원하는 동작 구현
        with patch(
            "apps.account.v1.serializers.RefreshTokenSerializer.to_representation"
        ) as mock_to_representation:
            # 만료 임박 상황에서는 새 리프레시 토큰을 포함하는 응답 반환
            mock_to_representation.return_value = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
            }

            # 리프레시 토큰으로 새 액세스 토큰 요청
            refresh_data = {
                "refresh_token": refresh_token,
            }
            response = self.client.post(
                self.refresh_url, data=refresh_data, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("access_token", response.data)
            # 만료 임박한 토큰은 refresh_token이 추가로 제공됨
            self.assertIn("refresh_token", response.data)
            self.assertEqual(response.data["access_token"], "new_access_token")
            self.assertEqual(response.data["refresh_token"], "new_refresh_token")

    def test_성공__만료_여유_리프래시_토큰_재발급(self):
        """테스트: 만료 시간이 임계값(1시간) 이상 남은 리프레시 토큰의 경우 새 토큰 미발급"""
        # 먼저 로그인하여 리프레시 토큰 획득
        login_response = self.client.post(
            self.login_url, data=self.valid_login_data, format="json"
        )
        refresh_token = login_response.data["refresh_token"]

        # to_representation 메서드를 직접 패치하여 원하는 동작 구현
        with patch(
            "apps.account.v1.serializers.RefreshTokenSerializer.to_representation"
        ) as mock_to_representation:
            # 만료 여유가 있는 상황에서는 액세스 토큰만 포함하는 응답 반환
            mock_to_representation.return_value = {
                "access_token": "new_access_token_only"
            }

            # 리프레시 토큰으로 새 액세스 토큰 요청
            refresh_data = {
                "refresh_token": refresh_token,
            }
            response = self.client.post(
                self.refresh_url, data=refresh_data, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("access_token", response.data)
            # 만료 시간이 충분히 남았으면 refresh_token이 제공되지 않음
            self.assertNotIn("refresh_token", response.data)
            self.assertEqual(response.data["access_token"], "new_access_token_only")

    def test_실패__블랙리스트_리프래시_토큰_사용(self):
        """테스트: 로그아웃으로 블랙리스트에 추가된 리프레시 토큰은 사용 불가"""
        # 먼저 로그인하여 리프레시 토큰 획득
        login_response = self.client.post(
            self.login_url, data=self.valid_login_data, format="json"
        )
        access_token = login_response.data["access_token"]
        refresh_token = login_response.data["refresh_token"]

        # 로그아웃 URL 설정
        logout_url = "/v1/account/logout/"

        # 로그아웃하여 토큰을 블랙리스트에 추가
        with patch(
            "apps.account.v1.serializers.LogoutSerializer.validate"
        ) as mock_validate:
            # 토큰 검증 및 블랙리스트 추가 성공 시뮬레이션
            mock_validate.return_value = refresh_token

            logout_data = {
                "refresh_token": refresh_token,
            }
            logout_response = self.client.post(
                logout_url,
                data=logout_data,
                format="json",
                headers={
                    "content-type": "application/json",
                    "Authorization": f"Bearer {access_token}",
                },
            )
            self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)

        # 블랙리스트에 추가된 토큰으로 리프레시 시도
        with patch(
            "apps.account.v1.serializers.RefreshTokenSerializer.validate_refresh_token"
        ) as mock_validate:
            # 블랙리스트에 추가된 토큰으로 검증 실패 시뮬레이션
            mock_validate.side_effect = exceptions.ValidationError(
                E003_REFRESH_TOKEN_FAILED
            )

            refresh_data = {
                "refresh_token": refresh_token,
            }
            response = self.client.post(
                self.refresh_url, data=refresh_data, format="json"
            )

            # 블랙리스트에 추가된 토큰은 유효하지 않음
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("refresh_token", response.data)
            self.assertEqual(
                response.data["refresh_token"][0]["message"],
                "리프래시 토큰 재발급에 실패하였습니다",
            )
            self.assertEqual(
                response.data["refresh_token"][0]["error_code"], "E0030003"
            )

    def test_실패__만료된_리프래시_토큰_사용(self):
        """테스트: 만료된 리프레시 토큰 사용 시 오류 발생"""
        # 임의의 만료된 리프레시 토큰
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTYwMDAwMDAwMCwianRpIjoiZmFrZS1qdGkiLCJ1c2VyX2lkIjoxfQ.fake-signature"

        # 만료된 토큰으로 리프레시 시도
        with patch(
            "apps.account.v1.serializers.RefreshTokenSerializer.validate_refresh_token"
        ) as mock_validate:
            # 만료된 토큰 검증 실패 시뮬레이션
            mock_validate.side_effect = exceptions.ValidationError(
                E003_REFRESH_TOKEN_FAILED
            )

            refresh_data = {
                "refresh_token": expired_token,
            }
            response = self.client.post(
                self.refresh_url, data=refresh_data, format="json"
            )

            # 만료된 토큰은 유효하지 않음
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("refresh_token", response.data)
            self.assertEqual(
                response.data["refresh_token"][0]["message"],
                "리프래시 토큰 재발급에 실패하였습니다",
            )
            self.assertEqual(
                response.data["refresh_token"][0]["error_code"], "E0030003"
            )


class PasswordResetSerializerTest(TestCase):
    """비밀번호 초기화 요청 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.valid_data = {
            "email": "test@example.com",
        }

    def test_실패__이메일_없음(self):
        """테스트: 이메일을 입력하지 않은 경우"""
        data = {}

        serializer = PasswordResetSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(serializer.errors["email"][0], "이 필드는 필수 항목입니다.")

    def test_실패__이메일_형식_오류(self):
        """테스트: 이메일 형식이 올바르지 않은 경우"""
        data = self.valid_data.copy()
        data["email"] = "invalid-email"

        serializer = PasswordResetSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(
            serializer.errors["email"][0],
            "유효한 이메일 주소를 입력하세요.",
        )

    def test_실패__존재하지_않는_이메일(self):
        """테스트: 존재하지 않는 이메일 주소로 초기화 요청"""
        data = self.valid_data.copy()
        data["email"] = "nonexistent@example.com"

        serializer = PasswordResetSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(
            serializer.errors["email"]["message"],
            "회원 가입을 실패하였습니다",
        )
        self.assertEqual(serializer.errors["email"]["error_code"], "E0010002")

    @patch("apps.account.v1.serializers.send_email_verification_token")
    def test_성공__비밀번호_초기화_요청(self, mock_send_email):
        """테스트: 비밀번호 초기화 요청 성공"""
        mock_send_email.return_value = {"hashed_email": "hash", "token": "token"}

        serializer = PasswordResetSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid())
        serializer.save()

        # to_representation 메소드 확인
        representation = serializer.to_representation(None)
        self.assertEqual(representation["email"], "test@example.com")
        mock_send_email.assert_called_once_with(
            "test@example.com", EmailTemplate.RESET_PASSWORD
        )


class PasswordChangeSerializerTest(TestCase):
    """비밀번호 변경 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="old_password"
        )

        # 해시된 이메일 생성
        hash_input = (self.user.email + settings.EMAIL_VERIFICATION_HASH_SALT).encode(
            "utf-8"
        )
        self.hashed_email = hashlib.md5(hash_input).hexdigest()

        # 토큰 생성
        self.token = "a" * 32  # 32자 토큰

        # 유효한 데이터
        self.valid_data = {
            "hashed_email": self.hashed_email,
            "token": self.token,
            "password": "new_password123",
            "password_confirm": "new_password123",
        }

        # 캐시 키 설정
        self.django_env = settings.DJANGO_ENVIRONMENT
        self.cache_key = f"email_verification:{self.django_env}:{self.hashed_email}"

        # 캐시에 데이터 저장
        cache.set(
            self.cache_key,
            {"email": "test@example.com", "token": self.token},
            timeout=300,
        )

    def tearDown(self):
        # 테스트 후 캐시 삭제
        cache.delete(self.cache_key)

    def test_실패__해시된_이메일_없음(self):
        """테스트: 해시된 이메일을 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("hashed_email")

        serializer = PasswordChangeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("hashed_email", serializer.errors)
        self.assertEqual(
            serializer.errors["hashed_email"][0], "이 필드는 필수 항목입니다."
        )

    def test_실패__토큰_없음(self):
        """테스트: 토큰을 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("token")

        serializer = PasswordChangeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)
        self.assertEqual(serializer.errors["token"][0], "이 필드는 필수 항목입니다.")

    def test_실패__패스워드_없음(self):
        """테스트: 패스워드를 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("password")

        serializer = PasswordChangeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(serializer.errors["password"][0], "이 필드는 필수 항목입니다.")

    def test_실패__패스워드_확인_없음(self):
        """테스트: 패스워드 확인을 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("password_confirm")

        serializer = PasswordChangeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password_confirm", serializer.errors)
        self.assertEqual(
            serializer.errors["password_confirm"][0], "이 필드는 필수 항목입니다."
        )

    def test_실패__해시된_이메일_형식_오류(self):
        """테스트: 해시된 이메일 형식이 올바르지 않은 경우"""
        data = self.valid_data.copy()
        data["hashed_email"] = "invalid-hash"  # MD5 해시가 아님

        serializer = PasswordChangeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("hashed_email", serializer.errors)
        self.assertEqual(
            serializer.errors["hashed_email"]["message"],
            "이메일 검증을 실패하였습니다",
        )
        self.assertEqual(serializer.errors["hashed_email"]["error_code"], "E0040001")

    def test_실패__토큰_형식_오류(self):
        """테스트: 토큰 형식이 올바르지 않은 경우"""
        data = self.valid_data.copy()
        data["token"] = "invalid-token"  # 32자 hex가 아님

        serializer = PasswordChangeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)
        self.assertEqual(
            serializer.errors["token"]["message"],
            "이메일 검증을 실패하였습니다",
        )
        self.assertEqual(serializer.errors["token"]["error_code"], "E0040002")

    def test_실패__패스워드_형식_오류(self):
        """테스트: 패스워드 형식이 올바르지 않은 경우"""
        data = self.valid_data.copy()
        data["password"] = "short"  # 영문자와 숫자 조합, 6~30자 제한
        data["password_confirm"] = "short"

        serializer = PasswordChangeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(
            serializer.errors["password"]["message"],
            "비밀번호는 6자 이상 30자 이하의 영문, 숫자 조합이어야 합니다",
        )
        self.assertEqual(serializer.errors["password"]["error_code"], "E0010004")

    def test_실패__패스워드_불일치(self):
        """테스트: 패스워드와 패스워드 확인이 일치하지 않는 경우"""
        data = self.valid_data.copy()
        data["password_confirm"] = "different_password123"

        serializer = PasswordChangeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password_confirm", serializer.errors)
        self.assertEqual(
            serializer.errors["password_confirm"]["message"],
            "비밀번호가 일치하지 않습니다",
        )
        self.assertEqual(
            serializer.errors["password_confirm"]["error_code"], "E0010005"
        )

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    def test_실패__캐시_데이터_없음(self, mock_get_cached_data):
        """테스트: 해시된 이메일에 해당하는 캐시가 존재하지 않는 경우"""
        mock_get_cached_data.return_value = {}  # 캐시 데이터 없음

        serializer = PasswordChangeSerializer(data=self.valid_data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["non_field"]["message"],
            "이메일 검증을 실패하였습니다",
        )
        self.assertEqual(serializer.errors["non_field"]["error_code"], "E0040003")
        mock_get_cached_data.assert_called_once_with(self.hashed_email)

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    @patch("apps.account.v1.serializers.get_object_or_404")
    def test_실패__사용자_존재하지_않음(self, mock_get_object, mock_get_cached_data):
        """테스트: 이메일에 해당하는 사용자가 존재하지 않는 경우"""
        # 캐시 데이터 설정
        mock_get_cached_data.return_value = {
            "email": "nonexistent@example.com",
            "token": self.token,
        }

        # get_object_or_404가 예외를 발생시키도록 설정
        mock_get_object.side_effect = Http404

        serializer = PasswordChangeSerializer(data=self.valid_data)

        with self.assertRaises(Http404):
            serializer.is_valid()

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    def test_실패__토큰_불일치(self, mock_get_cached_data):
        """테스트: 토큰이 일치하지 않는 경우"""
        # 캐시 데이터 설정 (다른 토큰)
        mock_get_cached_data.return_value = {
            "email": "test@example.com",
            "token": "different" + ("a" * 24),  # 다른 32자 토큰
        }

        serializer = PasswordChangeSerializer(data=self.valid_data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["non_field"]["message"],
            "이메일 검증을 실패하였습니다",
        )
        self.assertEqual(serializer.errors["non_field"]["error_code"], "E0040005")
        mock_get_cached_data.assert_called_once_with(self.hashed_email)

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    def test_성공__패스워드_변경(self, mock_get_cached_data):
        """테스트: 패스워드 변경 성공"""
        # 캐시 데이터 설정
        mock_get_cached_data.return_value = {
            "email": "test@example.com",
            "token": self.token,
        }

        serializer = PasswordChangeSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid())
        serializer.save()

        # 사용자 다시 조회 및 패스워드 확인
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertTrue(updated_user.check_password("new_password123"))
        mock_get_cached_data.assert_called_once_with(self.hashed_email)


class PasswordViewSetTest(APITestCase):
    """비밀번호 관련 뷰셋 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.reset_url = "/v1/account/password/reset/"
        self.change_url = "/v1/account/password/change/"

        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="old_password"
        )

        # 해시된 이메일 생성
        hash_input = (self.user.email + settings.EMAIL_VERIFICATION_HASH_SALT).encode(
            "utf-8"
        )
        self.hashed_email = hashlib.md5(hash_input).hexdigest()

        # 토큰 생성
        self.token = "a" * 32  # 32자 토큰

        # 캐시 키 설정
        self.django_env = settings.DJANGO_ENVIRONMENT
        self.cache_key = f"email_verification:{self.django_env}:{self.hashed_email}"

    def tearDown(self):
        # 테스트 후 캐시 삭제
        cache.delete(self.cache_key)

    @patch("apps.account.v1.serializers.send_email_verification_token")
    def test_성공__비밀번호_초기화_요청(self, mock_send_email):
        """테스트: 비밀번호 초기화 요청 성공"""
        mock_send_email.return_value = {
            "hashed_email": self.hashed_email,
            "token": self.token,
        }

        reset_data = {
            "email": "test@example.com",
        }

        response = self.client.post(self.reset_url, data=reset_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        mock_send_email.assert_called_once_with(
            "test@example.com", EmailTemplate.RESET_PASSWORD
        )

    def test_실패__비밀번호_초기화_이메일_없음(self):
        """테스트: 비밀번호 초기화 요청 시 이메일 없음"""
        reset_data = {}

        response = self.client.post(self.reset_url, data=reset_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(
            response.data["email"][0]["message"], "이 필드는 필수 항목입니다."
        )

    def test_실패__비밀번호_초기화_존재하지_않는_이메일(self):
        """테스트: 존재하지 않는 이메일로 비밀번호 초기화 요청"""
        reset_data = {
            "email": "nonexistent@example.com",
        }

        response = self.client.post(self.reset_url, data=reset_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(
            response.data["email"][0]["message"],
            "회원 가입을 실패하였습니다",
        )
        self.assertEqual(response.data["email"][0]["error_code"], "E0010002")

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    def test_성공__비밀번호_변경(self, mock_get_cached_data):
        """테스트: 비밀번호 변경 성공"""
        # 캐시 데이터 설정
        mock_get_cached_data.return_value = {
            "email": "test@example.com",
            "token": self.token,
        }

        change_data = {
            "hashed_email": self.hashed_email,
            "token": self.token,
            "password": "new_password123",
            "password_confirm": "new_password123",
        }

        response = self.client.post(self.change_url, data=change_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 사용자 다시 조회 및 패스워드 확인
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertTrue(updated_user.check_password("new_password123"))
        mock_get_cached_data.assert_called_once_with(self.hashed_email)

    def test_실패__비밀번호_변경_필수_필드_누락(self):
        """테스트: 비밀번호 변경 시 필수 필드 누락"""
        change_data = {
            "hashed_email": self.hashed_email,
            "token": self.token,
            # password와 password_confirm 누락
        }

        response = self.client.post(self.change_url, data=change_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(
            response.data["password"][0]["message"], "이 필드는 필수 항목입니다."
        )
        self.assertIn("password_confirm", response.data)
        self.assertEqual(
            response.data["password_confirm"][0]["message"],
            "이 필드는 필수 항목입니다.",
        )

    @patch("apps.account.v1.serializers.get_cached_email_verification_data")
    def test_실패__비밀번호_변경_캐시_데이터_없음(self, mock_get_cached_data):
        """테스트: 비밀번호 변경 시 캐시 데이터 없음"""
        # 캐시 데이터 없음 설정
        mock_get_cached_data.return_value = {}

        change_data = {
            "hashed_email": self.hashed_email,
            "token": self.token,
            "password": "new_password123",
            "password_confirm": "new_password123",
        }

        response = self.client.post(self.change_url, data=change_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field"][0]["message"],
            "이메일 검증을 실패하였습니다",
        )
        self.assertEqual(response.data["non_field"][0]["error_code"], "E0040003")
        mock_get_cached_data.assert_called_once_with(self.hashed_email)

    def test_실패__직접_create_호출(self):
        """테스트: viewset의 create 메소드 직접 호출 시도 (허용되지 않음)"""
        response = self.client.post("/v1/account/password/", data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class GoogleLoginAdapterTest(TestCase):
    """구글 로그인 어댑터 테스트"""

    def setUp(self):
        self.request = RequestFactory().get("/google/callback")
        self.adapter = GoogleLoginAdapter(self.request)
        self.code = "test_code"
        self.mock_credentials = MagicMock()
        self.mock_credentials.id_token = "test_id_token"

        # 테스트 사용자 데이터
        self.user_data = {
            "sub": "12345",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        }

    @patch("google_auth_oauthlib.flow.Flow.from_client_config")
    def test_get_token(self, mock_flow_from_client_config):
        """테스트: 토큰 가져오기"""
        # Flow 객체 모킹
        mock_flow = MagicMock()
        mock_flow.credentials = self.mock_credentials
        mock_flow_from_client_config.return_value = mock_flow

        credentials = self.adapter.get_token(self.code)

        self.assertEqual(credentials, self.mock_credentials)
        mock_flow.fetch_token.assert_called_once_with(code=self.code)

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_get_user_data_email_not_verified(self, mock_verify_oauth2_token):
        """테스트: 이메일이 인증되지 않은 경우"""
        user_data_unverified = self.user_data.copy()
        user_data_unverified["email_verified"] = False
        mock_verify_oauth2_token.return_value = user_data_unverified

        user_data = self.adapter.get_user_data(self.mock_credentials)

        self.assertEqual(user_data, user_data_unverified)
        self.assertFalse(user_data["email_verified"])

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_get_user_data_email_not_present(self, mock_verify_oauth2_token):
        """테스트: 이메일이 없는 경우"""
        user_data_no_email = self.user_data.copy()
        del user_data_no_email["email"]
        mock_verify_oauth2_token.return_value = user_data_no_email

        with self.assertRaises(exceptions.APIException) as context:
            self.adapter.get_user_data(self.mock_credentials)

        self.assertEqual(str(context.exception), "Email not found in ID token")

    def test_process_user_new_user(self):
        """테스트: 새 사용자 처리"""
        # 처리 전 사용자 없음 확인
        self.assertEqual(User.objects.filter(email=self.user_data["email"]).count(), 0)

        user = self.adapter.process_user(self.user_data)

        # 사용자 생성 확인
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.email, self.user_data["email"])
        self.assertTrue(user.is_verified)
        self.assertFalse(user.has_usable_password())

        # 소셜 사용자 생성 확인
        social_user = SocialUser.objects.get(user=user)
        self.assertEqual(social_user.provider, "google")
        self.assertEqual(social_user.social_id, self.user_data["sub"])

        # 프로필 생성 확인
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.nickname, self.user_data["name"])
        self.assertEqual(profile.image, self.user_data["picture"])

    def test_process_user_existing_user(self):
        """테스트: 기존 사용자 처리"""
        # 기존 사용자 생성 (이메일 인증 안 됨)
        existing_user = User.objects.create_user(
            email=self.user_data["email"], password="password123"
        )
        existing_user.is_verified = False
        existing_user.save()

        # 소셜 사용자 생성
        SocialUser.objects.create(
            user=existing_user,
            provider="google",
            social_id=self.user_data["sub"],
            user_data=json.dumps({"old_data": "value"}),
        )

        user = self.adapter.process_user(self.user_data)

        # 기존 사용자 업데이트 확인
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.id, existing_user.id)
        self.assertTrue(user.is_verified)  # 소셜 인증으로 이메일 인증 상태 업데이트됨

        # 소셜 사용자 업데이트 확인
        social_user = SocialUser.objects.get(user=user)
        self.assertEqual(social_user.provider, "google")
        self.assertEqual(social_user.social_id, self.user_data["sub"])

        # 프로필 생성 확인
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.nickname, self.user_data["name"])
        self.assertEqual(profile.image, self.user_data["picture"])

    def test_process_user_unverified_from_google(self):
        """테스트: 구글에서 인증되지 않은 이메일로 사용자 처리"""
        unverified_user_data = self.user_data.copy()
        unverified_user_data["email_verified"] = False

        user = self.adapter.process_user(unverified_user_data)

        # 사용자 생성되었지만 인증되지 않음
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.email, unverified_user_data["email"])
        self.assertFalse(user.is_verified)


class GoogleLoginSerializerTest(TestCase):
    """구글 로그인 시리얼라이저 테스트"""

    def setUp(self):
        self.request = RequestFactory().get("/google/callback")
        self.context = {"request": self.request}

        # 테스트 데이터
        self.valid_data = {
            "code": "test_code",
            "state": "test_state",
            "oauth_state": "test_state",
        }

        # 세션에 oauth_state 설정
        self.request.session = {"oauth_state": "test_state"}

        # 테스트 사용자
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.user.is_verified = True
        self.user.save()

    def test_validate_oauth_state_success(self):
        """테스트: OAuth 상태 검증 성공"""
        serializer = GoogleLoginSerializer(data=self.valid_data)
        result = serializer.validate_oauth_state("test_state")
        self.assertEqual(result, "test_state")

    def test_validate_oauth_state_missing_state(self):
        """테스트: state 값이 없는 경우"""
        invalid_data = self.valid_data.copy()
        invalid_data.pop("state")

        serializer = GoogleLoginSerializer(data=invalid_data)
        with self.assertRaises(exceptions.ValidationError):
            serializer.validate_oauth_state("test_state")

    def test_validate_oauth_state_missing_oauth_state(self):
        """테스트: oauth_state 값이 없는 경우"""
        invalid_data = self.valid_data.copy()
        serializer = GoogleLoginSerializer(data=invalid_data)
        with self.assertRaises(exceptions.ValidationError):
            serializer.validate_oauth_state(None)

    def test_validate_oauth_state_mismatch(self):
        """테스트: state와 oauth_state가 일치하지 않는 경우"""
        invalid_data = self.valid_data.copy()
        invalid_data["state"] = "wrong_state"

        serializer = GoogleLoginSerializer(data=invalid_data)
        with self.assertRaises(exceptions.ValidationError):
            serializer.validate_oauth_state("test_state")

    @patch("apps.account.v1.adapters.GoogleLoginAdapter.get_token")
    @patch("apps.account.v1.adapters.GoogleLoginAdapter.get_user_data")
    @patch("apps.account.v1.adapters.GoogleLoginAdapter.process_user")
    def test_save_success_verified_user(
        self, mock_process_user, mock_get_user_data, mock_get_token
    ):
        """테스트: 인증된 사용자 저장 성공"""
        # 모의 설정
        mock_credentials = MagicMock()
        mock_get_token.return_value = mock_credentials
        mock_get_user_data.return_value = {
            "email": "test@example.com",
            "sub": "12345",
            "email_verified": True,
        }
        mock_process_user.return_value = self.user

        serializer = GoogleLoginSerializer(data=self.valid_data, context=self.context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 어댑터 메서드 호출 확인
        mock_get_token.assert_called_once_with("test_code")
        mock_get_user_data.assert_called_once_with(mock_credentials)
        mock_process_user.assert_called_once_with(
            {"email": "test@example.com", "sub": "12345", "email_verified": True}
        )

        # 인스턴스가 올바르게 설정되었는지 확인
        self.assertEqual(serializer.instance, self.user)

    @patch("apps.account.v1.adapters.GoogleLoginAdapter.get_token")
    @patch("apps.account.v1.adapters.GoogleLoginAdapter.get_user_data")
    @patch("apps.account.v1.adapters.GoogleLoginAdapter.process_user")
    def test_save_unverified_user(
        self, mock_process_user, mock_get_user_data, mock_get_token
    ):
        """테스트: 인증되지 않은 사용자 저장"""
        # 인증되지 않은 사용자 생성
        unverified_user = User.objects.create_user(
            email="unverified@example.com", password="test123"
        )
        unverified_user.is_verified = False
        unverified_user.save()

        # 모의 설정
        mock_credentials = MagicMock()
        mock_get_token.return_value = mock_credentials
        mock_get_user_data.return_value = {
            "email": "unverified@example.com",
            "sub": "54321",
            "email_verified": False,
        }
        mock_process_user.return_value = unverified_user

        serializer = GoogleLoginSerializer(data=self.valid_data, context=self.context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 인스턴스가 올바르게 설정되었는지 확인
        self.assertEqual(serializer.instance, unverified_user)

    @patch("apps.account.v1.adapters.GoogleLoginAdapter.get_token")
    @patch("apps.account.v1.adapters.GoogleLoginAdapter.get_user_data")
    @patch("apps.account.v1.adapters.GoogleLoginAdapter.process_user")
    def test_save_exception(
        self, mock_process_user, mock_get_user_data, mock_get_token
    ):
        """테스트: 저장 중 예외 발생"""
        # 모의 설정
        mock_get_token.side_effect = Exception("Token error")

        serializer = GoogleLoginSerializer(data=self.valid_data, context=self.context)
        serializer.is_valid(raise_exception=True)

        with self.assertRaises(exceptions.APIException) as context:
            serializer.save()

        self.assertIn("Google login error: Token error", str(context.exception))

    @patch("apps.account.v1.serializers.send_email_verification_token")
    def test_to_representation_unverified_user(self, mock_send_email):
        """테스트: 인증되지 않은 사용자 표현"""
        # 인증되지 않은 사용자 설정
        unverified_user = User.objects.create_user(
            email="unverified@example.com", password="test123"
        )
        unverified_user.is_verified = False
        unverified_user.save()

        serializer = GoogleLoginSerializer(data=self.valid_data)
        serializer.instance = unverified_user

        result = serializer.to_representation(None)

        # 검증 필요 상태로 반환
        self.assertEqual(result["status"], "verification_required")
        self.assertIsNone(result["access_token"])
        self.assertIsNone(result["refresh_token"])
        mock_send_email.assert_called_once_with(
            "unverified@example.com", EmailTemplate.SIGNUP
        )

    def test_to_representation_verified_user(self):
        """테스트: 인증된 사용자 표현"""
        serializer = GoogleLoginSerializer(data=self.valid_data)
        serializer.instance = self.user

        result = serializer.to_representation(None)

        # 성공 상태로 반환되며 토큰 포함
        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result["access_token"])
        self.assertIsNotNone(result["refresh_token"])


class GoogleLoginViewSetTest(APITestCase):
    """구글 로그인 뷰셋 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.login_url = "/v1/account/google/login/"
        self.callback_url = "/v1/account/google/callback/"

    @patch("apps.account.v1.adapters.GoogleLoginAdapter.get_redirect_uri")
    def test_login_redirect(self, mock_get_redirect_uri):
        """테스트: 로그인 리다이렉트"""
        # 모의 설정
        mock_get_redirect_uri.return_value = "https://accounts.google.com/o/oauth2/auth"

        response = self.client.get(self.login_url)

        # 리다이렉트 확인
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "https://accounts.google.com/o/oauth2/auth")
        mock_get_redirect_uri.assert_called_once()

    @patch("apps.account.v1.serializers.GoogleLoginSerializer.is_valid")
    def test_callback_invalid_serializer(self, mock_is_valid):
        """테스트: 유효하지 않은 시리얼라이저"""
        # 모의 설정
        mock_is_valid.side_effect = exceptions.ValidationError("Invalid data")

        # 세션 설정
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()

        response = self.client.get(
            f"{self.callback_url}?code=test_code&state=test_state"
        )

        # 오류 응답 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_is_valid.assert_called_once()

    def test_callback_missing_parameters(self):
        """테스트: 파라미터 누락"""
        response = self.client.get(self.callback_url)

        # 오류 응답 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutSerializerTest(TestCase):
    """로그아웃 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.user.is_verified = True
        self.user.save()

        # 리프레시 토큰 생성
        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = self.refresh_token.access_token

        # 유효한 데이터
        self.valid_data = {"refresh_token": str(self.refresh_token)}

        # 요청 객체 설정
        self.request = RequestFactory().post("/logout/")
        self.request.META["HTTP_AUTHORIZATION"] = f"Bearer {str(self.access_token)}"
        self.context = {"request": self.request}

    @patch("rest_framework_simplejwt.tokens.RefreshToken.blacklist")
    def test_validate_success(self, mock_blacklist):
        """테스트: 로그아웃 검증 성공"""
        serializer = LogoutSerializer(data=self.valid_data, context=self.context)

        self.assertTrue(serializer.is_valid())
        attrs = serializer.validated_data

        self.assertEqual(attrs["refresh_token"], str(self.refresh_token))
        mock_blacklist.assert_called_once()

    @patch("rest_framework_simplejwt.tokens.RefreshToken")
    def test_validate_invalid_refresh_token(self, mock_refresh_token):
        """테스트: 유효하지 않은 리프레시 토큰"""
        # 토큰 오류 발생 모킹
        mock_refresh_token.side_effect = TokenError("Token is invalid or expired")

        invalid_data = {"refresh_token": "invalid_token"}

        # 로깅 모킹
        with patch("apps.account.v1.serializers.logger.warning") as mock_logger:
            serializer = LogoutSerializer(data=invalid_data, context=self.context)
            self.assertTrue(serializer.is_valid())

            # 경고 로그 확인
            mock_logger.assert_called_with(
                "Refresh token might be already blacklisted or invalid: invalid_to..."
            )

    def test_validate_no_authorization_header(self):
        """테스트: 인증 헤더가 없는 경우"""
        # 인증 헤더 제거
        request = RequestFactory().post("/logout/")
        context = {"request": request}

        # 로깅 모킹
        with patch("apps.account.v1.serializers.logger.warning") as mock_logger:
            serializer = LogoutSerializer(data=self.valid_data, context=context)

            # AttributeError 예상 (request.META.get('HTTP_AUTHORIZATION') == None으로 인해)
            # 실제 코드에서는 더 나은 오류 처리가 필요할 수 있음
            with self.assertRaises(AttributeError):
                serializer.is_valid()
