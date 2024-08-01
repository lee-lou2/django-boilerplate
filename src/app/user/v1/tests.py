from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from app.user.models import Device, User


class UserLoginAPITest(APITestCase):
    METHOD = "post"
    PATH = "/v1/user/login/"
    RESPONSE_FIELDS = ["access", "refresh"]

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(email="test@test.com", password="test123!")

    def test_login_success_response(self):
        response = getattr(self.client, self.METHOD)(
            self.PATH, data={"email": "test@test.com", "password": "test123!"}
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        # 응답 필드 테스트
        self.assertListEqual(
            sorted(self.RESPONSE_FIELDS),
            sorted(response.data.keys()),
            f"{self.__class__.__name__} 응답 필드 테스트 실패",
        )

    def test_login_failure_response_from_invalid_email(self):
        response = getattr(self.client, self.METHOD)(
            self.PATH, data={"email": "test2@test.com", "password": "test123!"}
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertDictEqual(
            {
                "email": ["인증정보가 일치하지 않습니다."],
                "password": ["인증정보가 일치하지 않습니다."],
            },
            response.data,
        )

    def test_login_failure_response_from_invalid_password(self):
        response = getattr(self.client, self.METHOD)(
            self.PATH, data={"email": "test@test.com", "password": "test123!!"}
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertDictEqual(
            {
                "email": ["인증정보가 일치하지 않습니다."],
                "password": ["인증정보가 일치하지 않습니다."],
            },
            response.data,
        )


class UserLogoutAPITest(APITestCase):
    METHOD = "post"
    PATH = "/v1/user/logout/"

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(email="test@test.com", password="test123!")
        Device.objects.create(user=user, uid="uid", token="token")

    def setUp(self):
        self.user = User.objects.get(email="test@test.com")
        self.client.force_authenticate(self.user)

    def test_logout_success_response(self):
        response = getattr(self.client, self.METHOD)(self.PATH)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual({}, response.data)

    def test_logout_success_response_together_uid(self):
        response = getattr(self.client, self.METHOD)(self.PATH, data={"uid": "uid"})

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertFalse(self.user.device_set.filter(uid="uid").exists())
        self.assertEqual({}, response.data)


class UserRefreshAPITest(APITestCase):
    METHOD = "post"
    PATH = "/v1/user/refresh/"
    RESPONSE_FIELDS = ["access", "refresh"]

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(email="test@test.com", password="test123!")

    def setUp(self) -> None:
        self.user = User.objects.get(email="test@test.com")
        self.client.force_authenticate(self.user)

    def test_refresh_success_response(self):
        refresh = RefreshToken.for_user(self.user)
        response = getattr(self.client, self.METHOD)(
            self.PATH, data={"refresh": str(refresh)}
        )

        # 응답 상태 코드 테스트
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code,
            f"{self.__class__.__name__} 응답 상태 코드 테스트 실패",
        )
        # 응답 필드 테스트
        self.assertListEqual(
            sorted(self.RESPONSE_FIELDS),
            sorted(response.data.keys()),
            f"{self.__class__.__name__} 응답 필드 테스트 실패",
        )
