from datetime import timedelta

from django.conf import settings
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.game.models import AttendanceCheck, GamePoint, PointReason
from apps.game.v1.serializers import AttendanceCheckSerializer
from apps.user.models import User

TEST_REWARD_POINTS = [5, 5, 5, 10, 10, 10, 100]


@override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
class AttendanceCheckSerializerTests(APITestCase):
    """AttendanceCheckSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        # 어제 출석 체크 생성
        yesterday = timezone.now().date() - timedelta(days=1)
        self.yesterday_check = AttendanceCheck.objects.create(
            user=self.user,
            check_in_date=yesterday,
            consecutive_days=1,
        )

    def test_성공__출석체크_정보가_올바르게_직렬화(self):
        """출석체크 정보가 올바르게 직렬화되는지 테스트"""
        serializer = AttendanceCheckSerializer(self.yesterday_check)
        data = serializer.data

        self.assertEqual(data["id"], self.yesterday_check.id)
        self.assertEqual(data["check_in_date"], str(self.yesterday_check.check_in_date))
        self.assertEqual(
            data["consecutive_days"], self.yesterday_check.consecutive_days
        )

    def test_성공__연속_일수_검증(self):
        """연속 일수 검증 성공 테스트"""
        serializer = AttendanceCheckSerializer(self.yesterday_check, data={})
        self.assertTrue(serializer.is_valid())
        # 어제 출석했으므로 연속 일수가 1 증가해야 함
        self.assertEqual(serializer.validated_data["consecutive_days"], 2)

    def test_성공__연속_일수_초기화__어제_체크인_아님(self):
        """어제 체크인이 아닌 경우 연속 일수 초기화 성공 테스트"""
        # 2일 전 출석체크로 변경
        self.yesterday_check.check_in_date = timezone.now().date() - timedelta(days=2)
        self.yesterday_check.save()

        serializer = AttendanceCheckSerializer(self.yesterday_check, data={})
        self.assertTrue(serializer.is_valid())
        # 어제 출석하지 않았으므로 연속 일수가 0으로 초기화되어야 함
        self.assertEqual(serializer.validated_data["consecutive_days"], 0)

    def test_성공__연속_일수_초기화__최대_일수_도달(self):
        """최대 연속 일수 도달 시 초기화 성공 테스트"""
        # 최대 연속 일수로 설정
        max_days = len(settings.ATTENDANCE_CHECK_REWARD_POINTS)
        self.yesterday_check.consecutive_days = max_days
        self.yesterday_check.save()

        serializer = AttendanceCheckSerializer(self.yesterday_check, data={})
        self.assertTrue(serializer.is_valid())
        # 최대 연속 일수에 도달했으므로 연속 일수가 0으로 초기화되어야 함
        self.assertEqual(serializer.validated_data["consecutive_days"], 0)

    def test_성공__출석체크_업데이트(self):
        """출석체크 업데이트 성공 테스트"""
        request = APIClient().request()
        request.user = self.user
        serializer = AttendanceCheckSerializer(
            self.yesterday_check, data={}, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())

        # 업데이트 수행
        updated_check = serializer.save()

        # 오늘 날짜로 새로운 출석체크가 생성되었는지 확인
        self.assertEqual(updated_check.check_in_date, timezone.now().date())
        self.assertEqual(updated_check.consecutive_days, 2)  # 연속 일수 증가

        # 포인트가 지급되었는지 확인
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).last()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, int(TEST_REWARD_POINTS[2]))


@override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
class AttendanceCheckViewSetTests(APITestCase):
    """AttendanceCheckViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # 어제 출석 체크 생성
        yesterday = timezone.now().date() - timedelta(days=1)
        self.yesterday_check = AttendanceCheck.objects.create(
            user=self.user,
            check_in_date=yesterday,
            consecutive_days=1,
        )

        # API 경로
        self.attendance_check_url = "/v1/game/attendance-check/"

    def test_성공__마지막_출석체크_조회(self):
        """마지막 출석체크 조회 성공 테스트"""
        response = self.client.get(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 마지막 출석체크 정보 확인
        self.assertEqual(response.data["id"], self.yesterday_check.id)
        self.assertEqual(
            response.data["check_in_date"], str(self.yesterday_check.check_in_date)
        )
        self.assertEqual(
            response.data["consecutive_days"], self.yesterday_check.consecutive_days
        )

    def test_성공__출석체크_참여(self):
        """출석체크 참여 성공 테스트"""
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 출석체크 결과 확인
        self.assertEqual(response.data["check_in_date"], str(timezone.now().date()))
        self.assertEqual(response.data["consecutive_days"], 2)  # 연속 일수 증가

        # 포인트가 지급되었는지 확인
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).last()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, TEST_REWARD_POINTS[2])

    def test_실패__중복_출석체크(self):
        """같은 날 중복 출석체크 실패 테스트"""
        # 첫 번째 출석체크
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["check_in_date"], str(timezone.now().date()))
        self.assertEqual(response.data["consecutive_days"], 2)

        # 두 번째 출석체크 (같은 날)
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["check_in_date"], str(timezone.now().date()))
        self.assertEqual(response.data["consecutive_days"], 2)

    def test_실패__미인증_사용자(self):
        """미인증 사용자 접근 거부 테스트"""
        # 클라이언트에서 인증 정보 제거
        self.client.force_authenticate(user=None)

        response = self.client.get(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_실패__PUT_메소드_거부(self):
        """PUT 메소드 거부 테스트"""
        response = self.client.put(self.attendance_check_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_성공__연속_일수에_따른_포인트_지급(self):
        """연속 일수에 따른 포인트 지급 테스트"""
        # 연속 3일차 설정
        self.yesterday_check.consecutive_days = 2
        self.yesterday_check.save()

        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3일차 포인트 지급 확인
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).last()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, int(TEST_REWARD_POINTS[3]))


class AttendanceCheckRoleAPIViewTests(APITestCase):
    """AttendanceCheckRoleAPIView 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # API 경로
        self.attendance_check_role_url = "/v1/game/attendance-check/role/"

    @override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
    def test_성공__출석체크_룰_조회(self):
        """출석체크 룰 조회 성공 테스트"""
        response = self.client.get(self.attendance_check_role_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 출석체크 룰이 반환되는지 확인
        self.assertEqual(response.data, TEST_REWARD_POINTS)

    def test_실패__미인증_사용자(self):
        """미인증 사용자 접근 거부 테스트"""
        # 클라이언트에서 인증 정보 제거
        self.client.force_authenticate(user=None)

        response = self.client.get(self.attendance_check_role_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GamePointTests(APITestCase):
    """GamePoint 모델 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

    @override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
    def test_성공__출석체크_포인트_지급(self):
        """출석체크를 통한 포인트 지급 테스트"""
        # 출석체크 생성
        AttendanceCheck.objects.create(
            user=self.user,
            check_in_date=timezone.now().date(),
            consecutive_days=0,
        )

        # 포인트 생성 확인
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).first()

        self.assertIsNotNone(point)
        self.assertEqual(point.point, int(TEST_REWARD_POINTS[0]))
        self.assertEqual(point.reason, PointReason.ATTENDANCE_CHECK)

    def test_성공__다양한_이유로_포인트_지급(self):
        """다양한 이유로 포인트 지급 테스트"""
        # 출석체크 포인트
        GamePoint.objects.create(
            user=self.user,
            point=10,
            reason=PointReason.ATTENDANCE_CHECK,
        )

        # 동전 뒤집기 포인트
        GamePoint.objects.create(
            user=self.user,
            point=5,
            reason=PointReason.COIN_FLIP,
        )

        # 포인트 개수 확인
        self.assertEqual(GamePoint.objects.filter(user=self.user).count(), 2)

        # 출석체크 포인트 확인
        attendance_point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).first()
        self.assertEqual(attendance_point.point, 10)

        # 동전 뒤집기 포인트 확인
        coin_flip_point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.COIN_FLIP
        ).first()
        self.assertEqual(coin_flip_point.point, 5)


class AttendanceCheckEdgeCaseTests(APITestCase):
    """AttendanceCheck 엣지 케이스 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # API 경로
        self.attendance_check_url = "/v1/game/attendance-check/"

    @override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
    def test_성공__첫_출석체크(self):
        """첫 출석체크 성공 테스트"""
        # 기존 출석체크 없음
        response = self.client.get(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), None)

        # 첫 출석체크 참여
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 출석체크 결과 확인
        self.assertEqual(response.data["check_in_date"], str(timezone.now().date()))
        self.assertEqual(response.data["consecutive_days"], 0)  # 첫 출석이므로 0

        # 포인트가 지급되었는지 확인
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).first()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, TEST_REWARD_POINTS[0])

    @override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
    def test_성공__연속_출석_최대치_후_리셋(self):
        """연속 출석 최대치 도달 후 리셋 테스트"""
        # 최대 연속 일수 - 1로 설정 (마지막 날짜)
        max_days = len(TEST_REWARD_POINTS) - 1
        yesterday = timezone.now().date() - timedelta(days=1)

        AttendanceCheck.objects.create(
            user=self.user,
            check_in_date=yesterday,
            consecutive_days=max_days,
        )

        # 출석체크 참여 (최대 일수 초과)
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 연속 일수가 0으로 리셋되었는지 확인
        self.assertEqual(response.data["consecutive_days"], 0)

        # 포인트가 지급되었는지 확인 (0일차 포인트)
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).last()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, int(TEST_REWARD_POINTS[0]))
