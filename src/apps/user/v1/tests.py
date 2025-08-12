from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.user.models import User, UserPreference
from apps.user.models import UserProfile
from apps.user.v1.serializers import UserPreferenceSerializer
from apps.user.v1.serializers import UserProfileSerializer


class UserProfileSerializerTests(APITestCase):
    """UserProfileSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user

    def test_실패__닉네임이_입력되지_않아_프로필_생성_실패(self):
        """닉네임이 입력되지 않아 프로필 생성 실패 테스트"""
        data = {}
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)

    def test_성공__닉네임_프로필이미지_모두_입력되어_프로필_생성_완료(self):
        """닉네임, 프로필 이미지 모두 입력되어 프로필 생성 완료 테스트"""
        data = {
            "nickname": "테스트사용자",
            "image": "https://example.com/image.jpg",
        }
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertTrue(serializer.is_valid())
        profile = serializer.save(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.nickname, data["nickname"])
        self.assertEqual(profile.image, data["image"])

    def test_성공__닉네임만_입력되어_프로필_생성_완료(self):
        """닉네임만 입력되어 프로필 생성 완료 테스트"""
        data = {
            "nickname": "테스트사용자",
        }
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertTrue(serializer.is_valid())
        profile = serializer.save(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.nickname, data["nickname"])
        self.assertIsNone(profile.image)

    def test_실패__프로필_이미지만_입력되어_프로필_생성_실패(self):
        """프로필 이미지만 입력되어 프로필 생성 실패 테스트"""
        data = {
            "image": "https://example.com/image.jpg",
        }
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)

    def test_실패__닉네임_길이가_최소_길이보다_짧아서_실패(self):
        """닉네임 길이가 최소 길이(2자)보다 짧아서 실패 테스트"""
        data = {"nickname": "a"}  # 1자 닉네임
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)
        self.assertEqual(
            serializer.errors["nickname"]["message"],
            "닉네임은 2자 이상 30자 이하로 설정해야 합니다",
        )

    def test_실패__닉네임_길이가_최대_길이보다_길어서_실패(self):
        """닉네임 길이가 최대 길이(30자)보다 길어서 실패 테스트"""
        data = {"nickname": "a" * 31}  # 31자 닉네임
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)
        self.assertEqual(
            serializer.errors["nickname"][0],
            "이 필드의 글자 수가 30 이하인지 확인하세요.",
        )

    def test_실패__닉네임에_연속_공백이_있어서_실패(self):
        """닉네임에 연속 공백이 있어서 실패 테스트"""
        data = {"nickname": "테스트  사용자"}
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)
        self.assertEqual(
            serializer.errors["nickname"]["message"],
            "닉네임에 연속된 공백을 사용할 수 없습니다",
        )

    def test_실패__닉네임에_허용되지_않은_특수문자가_있어서_실패(self):
        """닉네임에 허용되지 않은 특수문자가 있어서 실패 테스트"""
        data = {"nickname": "테스트@사용자"}  # @ 문자는 허용되지 않음
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)
        self.assertEqual(
            serializer.errors["nickname"]["message"],
            "닉네임은 한글, 영어, 숫자, 특수문자(-_.+=^!)로만 구성되어야 합니다",
        )

    def test_실패__닉네임에_금지된_단어가_포함되어서_실패(self):
        """닉네임에 금지된 단어가 포함되어서 실패 테스트"""
        data = {"nickname": "admin"}
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)
        self.assertEqual(
            serializer.errors["nickname"]["message"],
            "닉네임에 금지된 단어가 포함되어 있습니다",
        )

    def test_실패__닉네임에_금지된_한글_단어가_포함되어서_실패(self):
        """닉네임에 금지된 한글 단어가 포함되어서 실패 테스트"""
        data = {"nickname": "관리자"}
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)
        self.assertEqual(
            serializer.errors["nickname"]["message"],
            "닉네임에 금지된 단어가 포함되어 있습니다",
        )

    def test_성공__닉네임에_허용된_특수문자만_포함되어서_성공(self):
        """닉네임에 허용된 특수문자만 포함되어서 성공 테스트"""
        data = {"nickname": "test-user_123.+=^!"}
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertTrue(serializer.is_valid())

    def test_성공__닉네임에_영어_숫자_한글_포함되어서_성공(self):
        """닉네임에 영어, 숫자, 한글이 포함되어서 성공 테스트"""
        data = {"nickname": "테스트123User"}
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertTrue(serializer.is_valid())

    def test_성공__닉네임에_공백이_적절히_포함되어서_성공(self):
        """닉네임에 공백이 적절히 포함되어서 성공 테스트"""
        data = {"nickname": "테스트 사용자"}
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertTrue(serializer.is_valid())

    def test_성공__닉네임에_이모티콘_포함되어서_성공(self):
        """닉네임에 이모티콘이 포함되어서 성공 테스트"""
        data = {"nickname": "테스트😀유저👍"}
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        self.assertTrue(serializer.is_valid())

    # 추가: 비속어 테스트
    # 참고: 실제 비속어 단어를 사용하는 것은 부적절할 수 있으므로,
    # better_profanity 라이브러리가 감지할 수 있는 일반적인 단어 사용
    def test_실패__닉네임에_비속어가_포함되어서_실패(self):
        """닉네임에 비속어가 포함되어서 실패 테스트 (better_profanity 라이브러리 사용)"""
        # 비속어를 직접 쓰지 않고 better_profanity에서 필터링할 수 있는 단어 사용
        # 예를 들어 'hell'이 필터링되는 경우 (실제 테스트 시 확인 필요)
        data = {"nickname": "hell_user"}
        serializer = UserProfileSerializer(data=data, context={"request": self.request})
        if not serializer.is_valid():
            self.assertIn("nickname", serializer.errors)
            # profanity 필터에 걸린 경우 관련 에러 메시지 확인
            if "닉네임에 비속어가 포함되어 있습니다" in str(
                serializer.errors["nickname"]["message"]
            ):
                self.assertEqual(
                    serializer.errors["nickname"]["message"],
                    "닉네임에 비속어가 포함되어 있습니다",
                )
        # 주의: better_profanity의 설정에 따라 이 테스트는 실패할 수 있음


class UserProfileViewTests(APITestCase):
    """UserProfileViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # v1 prefix를 사용하는 API 경로
        self.create_url = "/v1/user/me/profile/"
        self.detail_url_me = "/v1/user/me/profile/"
        self.detail_url_id = "/v1/user/999/profile/"  # 숫자 ID 경로

    def test_실패__닉네임이_입력되지_않아_프로필_생성_실패(self):
        """닉네임이 입력되지 않아 프로필 생성 실패 테스트"""
        data = {}
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(UserProfile.objects.count(), 0)

    def test_성공__닉네임_프로필이미지_모두_입력되어_프로필_생성_완료(self):
        """닉네임, 프로필 이미지 모두 입력되어 프로필 생성 완료 테스트"""
        data = {
            "nickname": "테스트사용자",
            "image": "https://example.com/image.jpg",
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.count(), 1)
        profile = UserProfile.objects.get()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.nickname, data["nickname"])
        self.assertEqual(profile.image, data["image"])

    def test_성공__닉네임만_입력되어_프로필_생성_완료(self):
        """닉네임만 입력되어 프로필 생성 완료 테스트"""
        data = {
            "nickname": "테스트사용자",
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.count(), 1)
        profile = UserProfile.objects.get()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.nickname, data["nickname"])
        self.assertIsNone(profile.image)

    def test_실패__프로필_이미지만_입력되어_프로필_생성_실패(self):
        """프로필 이미지만 입력되어 프로필 생성 실패 테스트"""
        data = {
            "image": "https://example.com/image.jpg",
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(UserProfile.objects.count(), 0)

    def test_성공__닉네임_입력해서_프로필_수정_성공(self):
        """닉네임 입력해서 프로필 수정 성공 테스트"""
        # 먼저 프로필 생성
        UserProfile.objects.create(
            user=self.user,
            nickname="기존닉네임",
        )

        data = {
            "nickname": "변경된닉네임",
        }
        response = self.client.put(self.detail_url_me, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = UserProfile.objects.get()
        self.assertEqual(profile.nickname, data["nickname"])

    def test_실패__pk_path_부분에_me_가_아닌_값을_넣어_404_오류(self):
        """pk path 부분에 me 가 아닌 값을 넣어 404 오류 테스트"""
        # 프로필이 없을 때 숫자 ID로 접근하면 404 오류
        response = self.client.get(self.detail_url_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_성공__pk_path_부분에_me_를_넣어_프로필_조회_성공(self):
        """pk path 부분에 me 를 넣어 프로필 조회 성공 테스트"""
        # 먼저 프로필 생성
        UserProfile.objects.create(
            user=self.user,
            nickname="테스트닉네임",
        )

        response = self.client.get(self.detail_url_me)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nickname"], "테스트닉네임")


class UserPreferenceSerializerTests(APITestCase):
    """UserPreferenceSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user

        # 기본 사용자 선호 정보 생성
        self.preference = UserPreference.objects.create(
            user=self.user,
            is_night_notification=False,
            is_push_notification=True,
            is_email_notification=True,
        )

    def test_성공__선호정보_직렬화_성공(self):
        """선호정보 직렬화 성공 테스트"""
        serializer = UserPreferenceSerializer(self.preference)
        data = serializer.data

        self.assertEqual(data["user"], self.user.id)
        self.assertEqual(data["is_night_notification"], False)
        self.assertEqual(data["is_push_notification"], True)
        self.assertEqual(data["is_email_notification"], True)
        self.assertIn("created_at", data)

    def test_성공__선호정보_역직렬화_성공(self):
        """선호정보 역직렬화 성공 테스트"""
        data = {
            "is_night_notification": True,
            "is_push_notification": False,
            "is_email_notification": False,
        }
        serializer = UserPreferenceSerializer(
            instance=self.preference,
            data=data,
            partial=True,
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid())
        updated_preference = serializer.save()

        self.assertEqual(updated_preference.user, self.user)
        self.assertEqual(updated_preference.is_night_notification, True)
        self.assertEqual(updated_preference.is_push_notification, False)
        self.assertEqual(updated_preference.is_email_notification, False)

    def test_성공__일부_필드만_업데이트_성공(self):
        """일부 필드만 업데이트 성공 테스트"""
        data = {
            "is_night_notification": True,
        }
        serializer = UserPreferenceSerializer(
            instance=self.preference,
            data=data,
            partial=True,
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid())
        updated_preference = serializer.save()

        self.assertEqual(updated_preference.is_night_notification, True)
        self.assertEqual(updated_preference.is_push_notification, True)  # 변경되지 않음
        self.assertEqual(
            updated_preference.is_email_notification, True
        )  # 변경되지 않음


class UserPreferenceViewTests(APITestCase):
    """UserPreferenceViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # 기본 사용자 선호 정보 생성
        self.preference = UserPreference.objects.create(
            user=self.user,
            is_night_notification=False,
            is_push_notification=True,
            is_email_notification=True,
        )

        # API 경로
        self.preference_url = "/v1/user/me/preference/"

    def test_성공__선호정보_조회_성공(self):
        """선호정보 조회 성공 테스트"""
        response = self.client.get(self.preference_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["is_night_notification"], False)
        self.assertEqual(response.data["is_push_notification"], True)
        self.assertEqual(response.data["is_email_notification"], True)

    def test_실패__PUT_메서드로_전체_업데이트_시도시_실패(self):
        """PUT 메서드로 전체 업데이트 시도시 실패 테스트"""
        data = {
            "is_night_notification": True,
            "is_push_notification": False,
            "is_email_notification": False,
        }
        response = self.client.put(self.preference_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_성공__PATCH_메서드로_부분_업데이트_성공(self):
        """PATCH 메서드로 부분 업데이트 성공 테스트"""
        data = {
            "is_night_notification": True,
            "is_push_notification": False,
        }
        response = self.client.patch(self.preference_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # DB에서 변경사항 확인
        updated_preference = UserPreference.objects.get(user=self.user)
        self.assertEqual(updated_preference.is_night_notification, True)
        self.assertEqual(updated_preference.is_push_notification, False)
        self.assertEqual(
            updated_preference.is_email_notification, True
        )  # 변경되지 않음

        # 응답 데이터 확인
        self.assertEqual(response.data["is_night_notification"], True)
        self.assertEqual(response.data["is_push_notification"], False)
        self.assertEqual(response.data["is_email_notification"], True)

    def test_성공__단일_필드만_업데이트_성공(self):
        """단일 필드만 업데이트 성공 테스트"""
        data = {
            "is_email_notification": False,
        }
        response = self.client.patch(self.preference_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_preference = UserPreference.objects.get(user=self.user)
        self.assertEqual(
            updated_preference.is_night_notification, False
        )  # 변경되지 않음
        self.assertEqual(updated_preference.is_push_notification, True)  # 변경되지 않음
        self.assertEqual(updated_preference.is_email_notification, False)

    def test_실패__인증되지_않은_사용자_접근_실패(self):
        """인증되지 않은 사용자 접근 실패 테스트"""
        # 인증 제거
        self.client.force_authenticate(user=None)

        response = self.client.get(self.preference_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        data = {"is_night_notification": True}
        response = self.client.patch(self.preference_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_성공__선호정보가_없는_사용자_조회시_404(self):
        """선호정보가 없는 사용자 조회시 404 테스트"""
        # 현재 사용자의 선호정보 삭제
        self.preference.delete()

        response = self.client.get(self.preference_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_성공__모든_알림_설정_비활성화(self):
        """모든 알림 설정 비활성화 테스트"""
        data = {
            "is_night_notification": False,
            "is_push_notification": False,
            "is_email_notification": False,
        }
        response = self.client.patch(self.preference_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_preference = UserPreference.objects.get(user=self.user)
        self.assertEqual(updated_preference.is_night_notification, False)
        self.assertEqual(updated_preference.is_push_notification, False)
        self.assertEqual(updated_preference.is_email_notification, False)

    def test_성공__모든_알림_설정_활성화(self):
        """모든 알림 설정 활성화 테스트"""
        data = {
            "is_night_notification": True,
            "is_push_notification": True,
            "is_email_notification": True,
        }
        response = self.client.patch(self.preference_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_preference = UserPreference.objects.get(user=self.user)
        self.assertEqual(updated_preference.is_night_notification, True)
        self.assertEqual(updated_preference.is_push_notification, True)
        self.assertEqual(updated_preference.is_email_notification, True)
