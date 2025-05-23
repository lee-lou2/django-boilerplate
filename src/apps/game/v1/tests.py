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
    """Tests for AttendanceCheckSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        # Create yesterday's attendance check
        yesterday = timezone.now().date() - timedelta(days=1)
        self.yesterday_check = AttendanceCheck.objects.create(
            user=self.user,
            check_in_date=yesterday,
            consecutive_days=1,
        )

    def test_should_correctly_serialize_attendance_check_information(self):
        """Test if attendance check information is serialized correctly"""
        serializer = AttendanceCheckSerializer(self.yesterday_check)
        data = serializer.data

        self.assertEqual(data["id"], self.yesterday_check.id)
        self.assertEqual(data["check_in_date"], str(self.yesterday_check.check_in_date))
        self.assertEqual(
            data["consecutive_days"], self.yesterday_check.consecutive_days
        )

    def test_should_validate_consecutive_days_successfully(self):
        """Test successful validation of consecutive days"""
        serializer = AttendanceCheckSerializer(self.yesterday_check, data={})
        self.assertTrue(serializer.is_valid())
        # Since checked in yesterday, consecutive days should increment by 1
        self.assertEqual(serializer.validated_data["consecutive_days"], 2)

    def test_should_reset_consecutive_days_if_not_checked_in_yesterday(self):
        """Test successful reset of consecutive days if not checked in yesterday"""
        # Change to attendance check from 2 days ago
        self.yesterday_check.check_in_date = timezone.now().date() - timedelta(days=2)
        self.yesterday_check.save()

        serializer = AttendanceCheckSerializer(self.yesterday_check, data={})
        self.assertTrue(serializer.is_valid())
        # Since not checked in yesterday, consecutive days should reset to 0
        self.assertEqual(serializer.validated_data["consecutive_days"], 0)

    def test_should_reset_consecutive_days_on_reaching_max_days(self):
        """Test successful reset of consecutive days on reaching maximum days"""
        # Set to maximum consecutive days
        max_days = len(settings.ATTENDANCE_CHECK_REWARD_POINTS)
        self.yesterday_check.consecutive_days = max_days
        self.yesterday_check.save()

        serializer = AttendanceCheckSerializer(self.yesterday_check, data={})
        self.assertTrue(serializer.is_valid())
        # Since maximum consecutive days reached, consecutive days should reset to 0
        self.assertEqual(serializer.validated_data["consecutive_days"], 0)

    def test_should_update_attendance_check_successfully(self):
        """Test successful update of attendance check"""
        request = APIClient().request()
        request.user = self.user
        serializer = AttendanceCheckSerializer(
            self.yesterday_check, data={}, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())

        # Perform update
        updated_check = serializer.save()

        # Check if new attendance check for today is created
        self.assertEqual(updated_check.check_in_date, timezone.now().date())
        self.assertEqual(updated_check.consecutive_days, 2)  # Consecutive days incremented

        # Check if points were awarded
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).last()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, int(TEST_REWARD_POINTS[2]))


@override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
class AttendanceCheckViewSetTests(APITestCase):
    """Tests for AttendanceCheckViewSet"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create yesterday's attendance check
        yesterday = timezone.now().date() - timedelta(days=1)
        self.yesterday_check = AttendanceCheck.objects.create(
            user=self.user,
            check_in_date=yesterday,
            consecutive_days=1,
        )

        # API path
        self.attendance_check_url = "/v1/game/attendance-check/"

    def test_should_retrieve_last_attendance_check_successfully(self):
        """Test successful retrieval of last attendance check"""
        response = self.client.get(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check last attendance check information
        self.assertEqual(response.data["id"], self.yesterday_check.id)
        self.assertEqual(
            response.data["check_in_date"], str(self.yesterday_check.check_in_date)
        )
        self.assertEqual(
            response.data["consecutive_days"], self.yesterday_check.consecutive_days
        )

    def test_should_participate_in_attendance_check_successfully(self):
        """Test successful participation in attendance check"""
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check attendance check result
        self.assertEqual(response.data["check_in_date"], str(timezone.now().date()))
        self.assertEqual(response.data["consecutive_days"], 2)  # Consecutive days incremented

        # Check if points were awarded
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).last()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, TEST_REWARD_POINTS[2])

    def test_should_return_existing_check_on_duplicate_attendance_check_on_same_day(self):
        """Test failure of duplicate attendance check on the same day"""
        # First attendance check
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["check_in_date"], str(timezone.now().date()))
        self.assertEqual(response.data["consecutive_days"], 2)

        # Second attendance check (same day)
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["check_in_date"], str(timezone.now().date()))
        self.assertEqual(response.data["consecutive_days"], 2)

    def test_should_deny_access_for_unauthenticated_user(self):
        """Test access denial for unauthenticated user"""
        # Remove authentication information from client
        self.client.force_authenticate(user=None)

        response = self.client.get(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_should_reject_put_method(self):
        """Test rejection of PUT method"""
        response = self.client.put(self.attendance_check_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_should_award_points_based_on_consecutive_days(self):
        """Test awarding points based on consecutive days"""
        # Set to 3rd consecutive day
        self.yesterday_check.consecutive_days = 2
        self.yesterday_check.save()

        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if points for 3rd day were awarded
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).last()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, int(TEST_REWARD_POINTS[3]))


class AttendanceCheckRoleAPIViewTests(APITestCase):
    """Tests for AttendanceCheckRoleAPIView"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # API path
        self.attendance_check_role_url = "/v1/game/attendance-check/role/"

    @override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
    def test_should_retrieve_attendance_check_rules_successfully(self):
        """Test successful retrieval of attendance check rules"""
        response = self.client.get(self.attendance_check_role_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if attendance check rules are returned
        self.assertEqual(response.data, TEST_REWARD_POINTS)

    def test_should_deny_access_for_unauthenticated_user_when_retrieving_rules(self):
        """Test access denial for unauthenticated user when retrieving rules"""
        # Remove authentication information from client
        self.client.force_authenticate(user=None)

        response = self.client.get(self.attendance_check_role_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GamePointTests(APITestCase):
    """Tests for GamePoint model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

    @override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
    def test_should_award_points_for_attendance_check(self):
        """Test awarding points through attendance check"""
        # Create attendance check
        AttendanceCheck.objects.create(
            user=self.user,
            check_in_date=timezone.now().date(),
            consecutive_days=0,
        )

        # Check point creation
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).first()

        self.assertIsNotNone(point)
        self.assertEqual(point.point, int(TEST_REWARD_POINTS[0]))
        self.assertEqual(point.reason, PointReason.ATTENDANCE_CHECK)

    def test_should_award_points_for_various_reasons(self):
        """Test awarding points for various reasons"""
        # Attendance check points
        GamePoint.objects.create(
            user=self.user,
            point=10,
            reason=PointReason.ATTENDANCE_CHECK,
        )

        # Coin flip points
        GamePoint.objects.create(
            user=self.user,
            point=5,
            reason=PointReason.COIN_FLIP,
        )

        # Check number of points
        self.assertEqual(GamePoint.objects.filter(user=self.user).count(), 2)

        # Check attendance check points
        attendance_point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).first()
        self.assertEqual(attendance_point.point, 10)

        # Check coin flip points
        coin_flip_point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.COIN_FLIP
        ).first()
        self.assertEqual(coin_flip_point.point, 5)


class AttendanceCheckEdgeCaseTests(APITestCase):
    """Edge case tests for AttendanceCheck"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # API path
        self.attendance_check_url = "/v1/game/attendance-check/"

    @override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
    def test_should_handle_first_attendance_check_successfully(self):
        """Test successful handling of first attendance check"""
        # No existing attendance check
        response = self.client.get(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), None)

        # Participate in first attendance check
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check attendance check result
        self.assertEqual(response.data["check_in_date"], str(timezone.now().date()))
        self.assertEqual(response.data["consecutive_days"], 0)  # 0 for first attendance

        # Check if points were awarded
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).first()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, TEST_REWARD_POINTS[0])

    @override_settings(ATTENDANCE_CHECK_REWARD_POINTS=TEST_REWARD_POINTS)
    def test_should_reset_after_reaching_max_consecutive_attendance(self):
        """Test reset after reaching maximum consecutive attendance"""
        # Set to maximum consecutive days - 1 (last day)
        max_days = len(TEST_REWARD_POINTS) - 1
        yesterday = timezone.now().date() - timedelta(days=1)

        AttendanceCheck.objects.create(
            user=self.user,
            check_in_date=yesterday,
            consecutive_days=max_days,
        )

        # Participate in attendance check (exceeding max days)
        response = self.client.post(self.attendance_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if consecutive days reset to 0
        self.assertEqual(response.data["consecutive_days"], 0)

        # Check if points were awarded (points for day 0)
        point = GamePoint.objects.filter(
            user=self.user, reason=PointReason.ATTENDANCE_CHECK
        ).last()
        self.assertIsNotNone(point)
        self.assertEqual(point.point, int(TEST_REWARD_POINTS[0]))
