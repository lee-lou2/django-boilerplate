from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.agreement.models import (
    Agreement,
    UserAgreement,
    UserAgreementHistory,
    AgreementType,
)
from apps.agreement.v1.serializers import (
    AgreementSerializer,
    UserAgreementSerializer,
    UserAgreementCreateSerializer,
)
from apps.user.models import User


class AgreementSerializerTests(APITestCase):
    """AgreementSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.agreement = Agreement.objects.create(
            title="서비스 이용약관",
            content="서비스 이용약관 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.SERVICES,
            order=1,
            is_required=True,
            is_active=True,
        )

    def test_성공__약관_정보가_올바르게_직렬화(self):
        """약관 정보가 올바르게 직렬화되는지 테스트"""
        serializer = AgreementSerializer(self.agreement)
        data = serializer.data

        self.assertEqual(data["id"], self.agreement.id)
        self.assertEqual(data["title"], self.agreement.title)
        self.assertEqual(data["content"], self.agreement.content)
        self.assertEqual(data["version"], self.agreement.version)
        self.assertEqual(data["agreement_type"], self.agreement.agreement_type)
        self.assertEqual(data["order"], self.agreement.order)
        self.assertEqual(data["is_required"], self.agreement.is_required)


class UserAgreementSerializerTests(APITestCase):
    """UserAgreementSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user

        # 필수 동의 약관
        self.required_agreement = Agreement.objects.create(
            title="필수 약관",
            content="필수 약관 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.SERVICES,
            order=1,
            is_required=True,
            is_active=True,
        )

        # 선택 동의 약관
        self.optional_agreement = Agreement.objects.create(
            title="선택 약관",
            content="선택 약관 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.MARKETING,
            order=2,
            is_required=False,
            is_active=True,
        )

        # 사용자 약관 동의 정보
        self.user_agreement = UserAgreement.objects.create(
            user=self.user,
            agreement=self.required_agreement,
            is_agreed=True,
        )

    def test_실패__필수_약관에_미동의(self):
        """필수 약관에 미동의하면 유효성 검사 실패 테스트"""
        data = {"is_agreed": False}
        serializer = UserAgreementSerializer(
            instance=self.user_agreement,
            data=data,
            context={"request": self.request},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("is_agreed", serializer.errors)

    def test_성공__선택_약관에_미동의_가능(self):
        """선택 약관에는 미동의 가능 테스트"""
        optional_user_agreement = UserAgreement.objects.create(
            user=self.user,
            agreement=self.optional_agreement,
            is_agreed=True,
        )

        data = {"is_agreed": False}
        serializer = UserAgreementSerializer(
            instance=optional_user_agreement,
            data=data,
            context={"request": self.request},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())

    def test_성공__약관_업데이트시_히스토리_생성(self):
        """약관 동의 상태 업데이트 시 히스토리가 생성되는지 테스트"""
        # 히스토리 개수 초기화
        initial_history_count = UserAgreementHistory.objects.count()

        # 약관 동의 상태 업데이트
        data = {"is_agreed": True}  # 이미 True였지만, 다시 업데이트
        serializer = UserAgreementSerializer(
            instance=self.user_agreement,
            data=data,
            context={"request": self.request},
            partial=True,
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()

        # 히스토리가 생성되었는지 확인
        self.assertEqual(
            UserAgreementHistory.objects.count(), initial_history_count + 1
        )

        # 히스토리 내용 확인
        history = UserAgreementHistory.objects.last()
        self.assertEqual(history.user_agreement, self.user_agreement)
        self.assertEqual(history.data["is_agreed"], True)  # 이전 값이 저장되었는지


class UserAgreementCreateSerializerTests(APITestCase):
    """UserAgreementCreateSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user

        # 필수 동의 약관 1
        self.required_agreement1 = Agreement.objects.create(
            title="필수 약관 1",
            content="필수 약관 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.SERVICES,
            order=1,
            is_required=True,
            is_active=True,
        )

        # 필수 동의 약관 2
        self.required_agreement2 = Agreement.objects.create(
            title="필수 약관 2",
            content="개인정보 처리방침입니다.",
            version="1.0",
            agreement_type=AgreementType.PRIVACY,
            order=2,
            is_required=True,
            is_active=True,
        )

        # 선택 동의 약관
        self.optional_agreement = Agreement.objects.create(
            title="선택 약관",
            content="마케팅 정보 수신 동의입니다.",
            version="1.0",
            agreement_type=AgreementType.MARKETING,
            order=3,
            is_required=False,
            is_active=True,
        )

    def test_실패__약관_항목에_필드_누락(self):
        """약관 동의 항목에 필드가 누락된 경우 실패 테스트"""
        data = {
            "agreements": [
                {"id": self.required_agreement1.id},  # is_agreed 필드 누락
                {"is_agreed": True},  # id 필드 누락
            ]
        }
        serializer = UserAgreementCreateSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("agreements", serializer.errors)

    def test_실패__존재하지_않는_약관_ID(self):
        """존재하지 않는 약관 ID를 사용한 경우 실패 테스트"""
        data = {
            "agreements": [
                {"id": 9999, "is_agreed": True},  # 존재하지 않는 ID
                {"id": self.required_agreement1.id, "is_agreed": True},
                {"id": self.required_agreement2.id, "is_agreed": True},
                {"id": self.optional_agreement.id, "is_agreed": False},
            ]
        }
        serializer = UserAgreementCreateSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("agreements", serializer.errors)

    def test_실패__필수_약관_미동의(self):
        """필수 약관에 미동의한 경우 실패 테스트"""
        data = {
            "agreements": [
                {"id": self.required_agreement1.id, "is_agreed": True},
                {
                    "id": self.required_agreement2.id,
                    "is_agreed": False,
                },  # 필수지만 미동의
                {"id": self.optional_agreement.id, "is_agreed": False},
            ]
        }
        serializer = UserAgreementCreateSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("agreements", serializer.errors)

    def test_실패__일부_약관_누락(self):
        """일부 활성화된 약관이 누락된 경우 실패 테스트"""
        data = {
            "agreements": [
                {"id": self.required_agreement1.id, "is_agreed": True},
                {"id": self.required_agreement2.id, "is_agreed": True},
                # 선택 약관 누락
            ]
        }
        serializer = UserAgreementCreateSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("agreements", serializer.errors)

    def test_성공__모든_약관_동의_정상처리(self):
        """모든 약관에 대해 올바르게 동의한 경우 성공 테스트"""
        data = {
            "agreements": [
                {"id": self.required_agreement1.id, "is_agreed": True},
                {"id": self.required_agreement2.id, "is_agreed": True},
                {
                    "id": self.optional_agreement.id,
                    "is_agreed": False,
                },  # 선택 약관은 미동의 가능
            ]
        }
        serializer = UserAgreementCreateSerializer(
            data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())

        # create 메서드 실행 (bulk_create 호출)
        serializer.save()

        # 사용자 약관 동의 정보가 생성되었는지 확인
        self.assertEqual(UserAgreement.objects.filter(user=self.user).count(), 3)

        # 필수 약관은 동의했는지 확인
        self.assertTrue(
            UserAgreement.objects.get(
                user=self.user, agreement=self.required_agreement1
            ).is_agreed
        )

        self.assertTrue(
            UserAgreement.objects.get(
                user=self.user, agreement=self.required_agreement2
            ).is_agreed
        )

        # 선택 약관은 미동의 상태인지 확인
        self.assertFalse(
            UserAgreement.objects.get(
                user=self.user, agreement=self.optional_agreement
            ).is_agreed
        )


class AgreementViewSetTests(APITestCase):
    """AgreementViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()

        # 활성화된 약관들 생성
        self.agreement1 = Agreement.objects.create(
            title="서비스 이용약관",
            content="서비스 이용약관 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.SERVICES,
            order=1,
            is_required=True,
            is_active=True,
        )

        self.agreement2 = Agreement.objects.create(
            title="개인정보 처리방침",
            content="개인정보 처리방침 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.PRIVACY,
            order=2,
            is_required=True,
            is_active=True,
        )

        # 비활성화된 약관 생성
        self.inactive_agreement = Agreement.objects.create(
            title="구 버전 약관",
            content="더 이상 사용되지 않는 약관입니다.",
            version="0.9",
            agreement_type=AgreementType.SERVICES,
            order=3,
            is_required=True,
            is_active=False,
        )

        # API 경로
        self.agreement_list_url = "/v1/account/agreement/"

    def test_성공__활성화된_약관_목록_조회(self):
        """활성화된 약관 목록 조회 성공 테스트"""
        response = self.client.get(self.agreement_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터에 활성화된 약관만 포함되어 있는지 확인
        self.assertEqual(response.data["count"], 2)

        # 응답 데이터의 결과가 order 필드 기준으로 정렬되었는지 확인
        self.assertEqual(response.data["results"][0]["id"], self.agreement1.id)
        self.assertEqual(response.data["results"][1]["id"], self.agreement2.id)

        # 비활성화된 약관이 포함되어 있지 않은지 확인
        inactive_ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(self.inactive_agreement.id, inactive_ids)

    def test_성공__미인증_사용자도_약관_조회_가능(self):
        """미인증 사용자도 약관 목록 조회 가능 테스트"""
        # 클라이언트에서 인증 정보를 제거
        self.client.force_authenticate(user=None)

        response = self.client.get(self.agreement_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)


class UserAgreementViewSetTests(APITestCase):
    """UserAgreementViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # 약관 생성
        self.required_agreement1 = Agreement.objects.create(
            title="서비스 이용약관",
            content="서비스 이용약관 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.SERVICES,
            order=1,
            is_required=True,
            is_active=True,
        )

        self.required_agreement2 = Agreement.objects.create(
            title="개인정보 처리방침",
            content="개인정보 처리방침 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.PRIVACY,
            order=2,
            is_required=True,
            is_active=True,
        )

        self.optional_agreement = Agreement.objects.create(
            title="마케팅 정보 수신 동의",
            content="마케팅 정보 수신 동의 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.MARKETING,
            order=3,
            is_required=False,
            is_active=True,
        )

        # 사용자 약관 동의 정보 생성
        self.user_agreement = UserAgreement.objects.create(
            user=self.user,
            agreement=self.required_agreement1,
            is_agreed=True,
        )

        # API 경로
        self.user_agreement_list_url = "/v1/user/me/agreement/"
        self.user_agreement_detail_url = (
            f"/v1/user/me/agreement/{self.user_agreement.id}/"
        )

    def test_성공__사용자_약관_목록_조회(self):
        """사용자 약관 목록 조회 성공 테스트"""
        response = self.client.get(self.user_agreement_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 사용자의 약관 수와 일치하는지 확인
        self.assertEqual(len(response.data), 1)

        # 사용자 약관 데이터 확인
        self.assertEqual(response.data[0]["id"], self.user_agreement.id)
        self.assertEqual(response.data[0]["is_agreed"], True)
        self.assertEqual(
            response.data[0]["agreement"]["id"], self.required_agreement1.id
        )

    def test_실패__인증되지_않은_사용자_접근_거부(self):
        """인증되지 않은 사용자 접근 거부 테스트"""
        # 클라이언트에서 인증 정보 제거
        self.client.force_authenticate(user=None)

        response = self.client.get(self.user_agreement_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_성공__약관_동의_생성(self):
        """약관 동의 생성 성공 테스트"""
        self.user_agreement.delete()
        data = {
            "agreements": [
                {"id": self.required_agreement1.id, "is_agreed": True},
                {"id": self.required_agreement2.id, "is_agreed": True},
                {"id": self.optional_agreement.id, "is_agreed": False},
            ]
        }

        response = self.client.post(self.user_agreement_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 새로운 사용자 약관 동의 정보가 생성되었는지 확인
        self.assertEqual(UserAgreement.objects.filter(user=self.user).count(), 3)

        # 선택 약관은 미동의 상태로 저장되었는지 확인
        optional_ua = UserAgreement.objects.get(
            user=self.user, agreement=self.optional_agreement
        )
        self.assertFalse(optional_ua.is_agreed)

    def test_실패__약관_동의_생성시_필수_약관_미동의(self):
        """약관 동의 생성 시 필수 약관 미동의 실패 테스트"""
        data = {
            "agreements": [
                {"id": self.required_agreement1.id, "is_agreed": True},
                {
                    "id": self.required_agreement2.id,
                    "is_agreed": False,
                },  # 필수 약관 미동의
                {"id": self.optional_agreement.id, "is_agreed": False},
            ]
        }

        response = self.client.post(self.user_agreement_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_성공__약관_동의_부분_업데이트(self):
        """약관 동의 부분 업데이트 성공 테스트"""
        # 먼저 모든 약관에 대한 동의 정보 생성
        UserAgreement.objects.all().delete()  # 기존 데이터 정리

        for agreement in [
            self.required_agreement1,
            self.required_agreement2,
            self.optional_agreement,
        ]:
            UserAgreement.objects.create(
                user=self.user,
                agreement=agreement,
                is_agreed=True if agreement.is_required else False,
            )

        # 선택 약관 가져오기
        optional_user_agreement = UserAgreement.objects.get(
            user=self.user, agreement=self.optional_agreement
        )

        # 선택 약관 동의 상태 업데이트
        data = {"is_agreed": True}

        response = self.client.patch(
            f"/v1/user/me/agreement/{optional_user_agreement.id}/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 업데이트된 동의 상태 확인
        optional_user_agreement.refresh_from_db()
        self.assertTrue(optional_user_agreement.is_agreed)

        # 히스토리가 생성되었는지 확인
        self.assertTrue(
            UserAgreementHistory.objects.filter(
                user_agreement=optional_user_agreement
            ).exists()
        )

    def test_실패__PUT_메소드_거부(self):
        """PUT 메소드 거부 테스트"""
        data = {"is_agreed": False}

        response = self.client.put(self.user_agreement_detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


from django.core.cache import cache
from django.test import override_settings
from unittest.mock import patch
from apps.agreement.v1.tasks import task_send_re_agreement_notification
from apps.agreement.v1.paginations import AgreementLimitOffsetPagination


class AgreementModelTests(APITestCase):
    """Agreement 모델 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.agreement = Agreement.objects.create(
            title="서비스 이용약관",
            content="서비스 이용약관 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.SERVICES,
            order=1,
            is_required=True,
            is_active=True,
        )

    def test_실패__약관_수정_불가(self):
        """약관은 수정할 수 없고 새 버전으로 등록해야 함을 테스트"""
        # 기존 약관 조회
        agreement = Agreement.objects.get(id=self.agreement.id)

        # 약관 내용 수정 시도
        agreement.content = "수정된 약관 내용입니다."

        # ValueError가 발생하는지 확인
        with self.assertRaises(ValueError) as context:
            agreement.save()

        # 에러 메시지 확인
        self.assertIn("약관은 수정할 수 없습니다", str(context.exception))

        # 데이터베이스에 저장된 값이 변경되지 않았는지 확인
        agreement.refresh_from_db()
        self.assertEqual(agreement.content, "서비스 이용약관 내용입니다.")

    def test_성공__약관_타입_확인(self):
        """약관 타입이 올바르게 저장되고 조회되는지 테스트"""
        # 서비스 약관
        service_agreement = Agreement.objects.create(
            title="서비스 약관",
            content="서비스 약관 내용",
            version="1.0",
            agreement_type=AgreementType.SERVICES,
            order=10,
            is_active=True,
        )
        self.assertEqual(service_agreement.agreement_type, AgreementType.SERVICES)
        self.assertEqual(service_agreement.get_agreement_type_display(), "서비스 약관")

        # 개인정보 처리방침
        privacy_agreement = Agreement.objects.create(
            title="개인정보 처리방침",
            content="개인정보 처리방침 내용",
            version="1.0",
            agreement_type=AgreementType.PRIVACY,
            order=20,
            is_active=True,
        )
        self.assertEqual(privacy_agreement.agreement_type, AgreementType.PRIVACY)
        self.assertEqual(
            privacy_agreement.get_agreement_type_display(), "개인정보 처리 방침"
        )

        # 마케팅 약관
        marketing_agreement = Agreement.objects.create(
            title="마케팅 약관",
            content="마케팅 약관 내용",
            version="1.0",
            agreement_type=AgreementType.MARKETING,
            order=30,
            is_active=True,
        )
        self.assertEqual(marketing_agreement.agreement_type, AgreementType.MARKETING)
        self.assertEqual(
            marketing_agreement.get_agreement_type_display(), "마케팅 약관"
        )


class UserAgreementHistoryTests(APITestCase):
    """UserAgreementHistory 모델 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.agreement = Agreement.objects.create(
            title="서비스 이용약관",
            content="서비스 이용약관 내용입니다.",
            version="1.0",
            agreement_type=AgreementType.SERVICES,
            order=1,
            is_required=True,
            is_active=True,
        )
        self.user_agreement = UserAgreement.objects.create(
            user=self.user,
            agreement=self.agreement,
            is_agreed=True,
        )


class AgreementPaginationTests(APITestCase):
    """약관 페이지네이션 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        # 약관 데이터 생성 (order 순서대로)
        for i in range(1, 15):
            Agreement.objects.create(
                title=f"테스트 약관 {i}",
                content=f"테스트 약관 내용 {i}",
                version="1.0",
                agreement_type=(
                    AgreementType.SERVICES
                    if i % 3 == 0
                    else (
                        AgreementType.PRIVACY if i % 3 == 1 else AgreementType.MARKETING
                    )
                ),
                order=i,
                is_required=(i % 2 == 0),  # 짝수 번호는 필수
                is_active=True,
            )

        self.pagination = AgreementLimitOffsetPagination()
        self.request_factory = RequestFactory()
