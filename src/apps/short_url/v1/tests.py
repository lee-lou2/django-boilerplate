from unittest import mock

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.short_url.models import ShortUrl
from apps.short_url.v1.serializers import ShortUrlSerializer
from apps.short_url.v1.utils import id_to_key, key_to_id
from apps.user.models import User
from common.enums.errors import E005_HASHED_VALUE_ALREADY_EXISTS


class ShortUrlSerializerTestCase(TestCase):
    """단축 URL 시리얼라이저 테스트 케이스"""

    def setUp(self):
        """테스트에 사용할 유효한 데이터 설정"""
        self.valid_data = {
            "ios_deep_link": "app://test",
            "ios_fallback_url": "https://example.com/ios",
            "android_deep_link": "app://test",
            "android_fallback_url": "https://example.com/android",
            "default_fallback_url": "https://example.com",
            "og_tag": {
                "title": "Test Title",
                "description": "Test Description",
                "image": "https://example.com/image.jpg",
            },
        }

    def test_성공__유효한_iOS_딥링크(self):
        """유효한 iOS 딥링크로 성공적으로 단축 URL을 생성하는지 테스트"""
        data = self.valid_data.copy()

        serializer = ShortUrlSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.ios_deep_link, data["ios_deep_link"])

    def test_성공__유효한_Android_딥링크(self):
        """유효한 Android 딥링크로 성공적으로 단축 URL을 생성하는지 테스트"""
        data = self.valid_data.copy()

        serializer = ShortUrlSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.android_deep_link, data["android_deep_link"])

    def test_성공__유효한_기본_폴백_URL(self):
        """유효한 기본 폴백 URL로 성공적으로 단축 URL을 생성하는지 테스트"""
        data = self.valid_data.copy()

        serializer = ShortUrlSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.default_fallback_url, data["default_fallback_url"])

    def test_실패__유효하지_않은_기본_폴백_URL(self):
        """유효하지 않은 기본 폴백 URL로 단축 URL 생성이 실패하는지 테스트"""
        data = self.valid_data.copy()
        data["default_fallback_url"] = "invalid-url"  # 유효하지 않은 URL 형식

        serializer = ShortUrlSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("default_fallback_url", serializer.errors)

    def test_실패__유효하지_않은_iOS_폴백_URL(self):
        """유효하지 않은 iOS 폴백 URL로 단축 URL 생성이 실패하는지 테스트"""
        data = self.valid_data.copy()
        data["ios_fallback_url"] = "invalid-url"  # 유효하지 않은 URL 형식

        serializer = ShortUrlSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("ios_fallback_url", serializer.errors)

    def test_실패__유효하지_않은_Android_폴백_URL(self):
        """유효하지 않은 Android 폴백 URL로 단축 URL 생성이 실패하는지 테스트"""
        data = self.valid_data.copy()
        data["android_fallback_url"] = "invalid-url"  # 유효하지 않은 URL 형식

        serializer = ShortUrlSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("android_fallback_url", serializer.errors)

    def test_성공__유효한_iOS_폴백_URL(self):
        """유효한 iOS 폴백 URL로 성공적으로 단축 URL을 생성하는지 테스트"""
        data = self.valid_data.copy()

        serializer = ShortUrlSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.ios_fallback_url, data["ios_fallback_url"])

    def test_성공__유효한_Android_폴백_URL(self):
        """유효한 Android 폴백 URL로 성공적으로 단축 URL을 생성하는지 테스트"""
        data = self.valid_data.copy()

        serializer = ShortUrlSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.android_fallback_url, data["android_fallback_url"])

    def test_성공__유효한_OG_태그(self):
        """유효한 OG 태그로 성공적으로 단축 URL을 생성하는지 테스트"""
        data = self.valid_data.copy()

        serializer = ShortUrlSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.og_tag, data["og_tag"])

    def test_실패__유효하지_않은_OG_태그(self):
        """유효하지 않은 OG 태그로 단축 URL 생성이 실패하는지 테스트"""
        data = self.valid_data.copy()
        data["og_tag"] = "not-a-json"  # JSON이 아닌 문자열

        serializer = ShortUrlSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("og_tag", serializer.errors)

    def test_실패__기본_폴백_URL_없음(self):
        """기본 폴백 URL이 없을 때 단축 URL 생성이 실패하는지 테스트"""
        data = self.valid_data.copy()
        data.pop("default_fallback_url")  # 기본 폴백 URL 제거

        serializer = ShortUrlSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("default_fallback_url", serializer.errors)

    def test_실패__해시값_중복(self):
        """동일한 해시값을 가진 단축 URL 생성이 실패하는지 테스트"""
        # 첫 번째 URL 생성
        serializer1 = ShortUrlSerializer(data=self.valid_data)
        self.assertTrue(serializer1.is_valid())
        instance1 = serializer1.save()

        # 두 번째 URL 생성 시도 (같은 데이터로)
        serializer2 = ShortUrlSerializer(data=self.valid_data)
        self.assertFalse(serializer2.is_valid())

        # 에러 메시지 확인
        self.assertIn("non_field", serializer2.errors)
        error_found = False
        for _, value in serializer2.errors["non_field"].items():
            if E005_HASHED_VALUE_ALREADY_EXISTS["non_field"]["message"] in str(value):
                error_found = True
                break

        self.assertTrue(error_found, "해시값 중복 에러 메시지가 없습니다.")


class ShortUrlViewSetTestCase(APITestCase):
    """단축 URL 뷰셋 테스트 케이스"""

    def setUp(self):
        """테스트에 사용할 클라이언트와 데이터 설정"""
        self.client = APIClient()
        self.url = reverse("short-url-list")

        # 테스트 사용자 생성 및 인증
        self.user = User.objects.create_user(email="test@test.com", password="test")
        self.client.force_authenticate(user=self.user)

        self.valid_data = {
            "ios_deep_link": "app://test",
            "ios_fallback_url": "https://example.com/ios",
            "android_deep_link": "app://test",
            "android_fallback_url": "https://example.com/android",
            "default_fallback_url": "https://example.com",
            "og_tag": {
                "title": "Test Title",
                "description": "Test Description",
                "image": "https://example.com/image.jpg",
            },
        }

    def test_인증_필요(self):
        """인증되지 않은 사용자의 단축 URL 생성 요청이 거부되는지 테스트"""
        self.client.logout()  # 인증 해제

        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_성공__단축URL_생성(self):
        """인증된 사용자의 유효한 데이터로 단축 URL 생성이 성공하는지 테스트"""
        with mock.patch(
            "apps.short_url.v1.serializers.generate_random_key", return_value="abcd"
        ):
            response = self.client.post(self.url, self.valid_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # 응답에 short_key가 포함되어 있는지 확인
            self.assertIn("short_key", response.data)

            # 데이터베이스에 저장되었는지 확인
            self.assertTrue(ShortUrl.objects.filter(id=response.data["id"]).exists())

    def test_실패__유효하지_않은_데이터(self):
        """인증된 사용자의 유효하지 않은 데이터로 단축 URL 생성이 실패하는지 테스트"""
        invalid_data = self.valid_data.copy()
        invalid_data["default_fallback_url"] = "invalid-url"

        response = self.client.post(self.url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UtilsTestCase(TestCase):
    """유틸리티 함수 테스트 케이스"""

    def test_id_to_key(self):
        """ID를 키로 변환하는 함수가 올바르게 작동하는지 테스트"""
        test_cases = [
            (1, "a"),
            (2, "b"),
            (63, "aa"),
            (64, "ab"),
            (100, "aL"),
        ]

        for id_value, expected_key in test_cases:
            self.assertEqual(id_to_key(id_value), expected_key)

        # 0 이하의 ID에 대해 None을 반환하는지 확인
        self.assertIsNone(id_to_key(0))
        self.assertIsNone(id_to_key(-1))

    def test_key_to_id(self):
        """키를 ID로 변환하는 함수가 올바르게 작동하는지 테스트"""
        test_cases = [
            ("a", 1),
            ("b", 2),
            ("10", 3401),
            ("11", 3402),
            ("1b", 3350),
        ]

        for key, expected_id in test_cases:
            self.assertEqual(key_to_id(key), expected_id)

        # 유효하지 않은 문자가 포함된 키에 대해 None을 반환하는지 확인
        self.assertIsNone(key_to_id("$"))
        self.assertIsNone(key_to_id("한글"))

    def test_generate_random_key(self):
        """랜덤 키 생성 함수가 올바른 형식의 키를 생성하는지 테스트"""
        from apps.short_url.v1.utils import generate_random_key

        for _ in range(10):  # 여러 번 테스트
            key = generate_random_key()

            # 키의 길이가 4여야 함
            self.assertEqual(len(key), 4)

            # 키는 영문자와 숫자로만
            import re

            self.assertTrue(re.match(r"^[a-zA-Z0-9]+$", key))
