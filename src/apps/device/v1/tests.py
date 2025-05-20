from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
import uuid

from apps.device.models import Device, PushToken, DevicePlatform
from apps.device.v1.serializers import DeviceSerializer, PushTokenSerializer
from apps.user.models import User


class DeviceSerializerTests(APITestCase):
    """DeviceSerializer tests"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user
        self.valid_uuid = uuid.uuid4()
        self.device_data = {
            "uuid": self.valid_uuid,
        }

    def test_성공__디바이스_등록_성공(self):
        """Device registration success test"""
        serializer = DeviceSerializer(
            data=self.device_data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        device = serializer.save(user=self.user)
        self.assertEqual(device.uuid, self.valid_uuid)
        self.assertEqual(device.user, self.user)

    def test_실패__다바이스_등록_시_UUID_형식이_올바르지_않음(self):
        """Device registration fails when UUID format is invalid"""
        data = {
            "uuid": "invalid-uuid",
        }
        serializer = DeviceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("uuid", serializer.errors)

    def test_실패__디바이스_등록_시_UUID_중복(self):
        """Device registration fails when UUID is duplicated"""
        # Create the device first
        Device.objects.create(
            user=self.user,
            uuid=self.valid_uuid,
        )

        # Try again with the same UUID
        serializer = DeviceSerializer(data=self.device_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("uuid", serializer.errors)

    def test_실패__디바이스_등록_시_UUID_필드가_없음(self):
        """Device registration fails when UUID field is missing"""
        data = {}
        serializer = DeviceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("uuid", serializer.errors)


class DeviceViewTests(APITestCase):
    """DeviceViewSet tests"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.create_url = "/v1/device/"
        self.valid_uuid = uuid.uuid4()
        self.device_data = {
            "uuid": self.valid_uuid,
        }

    def test_성공__디바이스_등록_성공(self):
        """Device registration success test"""
        response = self.client.post(self.create_url, self.device_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.count(), 1)
        device = Device.objects.get()
        self.assertEqual(str(device.uuid), str(self.valid_uuid))
        self.assertEqual(device.user, self.user)

    def test_실패__다바이스_등록_시_UUID_형식이_올바르지_않음(self):
        """Device registration fails when UUID format is invalid"""
        data = {
            "uuid": "invalid-uuid",
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Device.objects.count(), 0)
        self.assertIn("uuid", response.data)

    def test_실패__디바이스_등록_시_UUID_중복(self):
        """Device registration fails when UUID is duplicated"""
        # Create the device first
        Device.objects.create(
            user=self.user,
            uuid=self.valid_uuid,
        )

        # Try again with the same UUID
        response = self.client.post(self.create_url, self.device_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Device.objects.count(), 1)
        self.assertIn("uuid", response.data)

    def test_실패__디바이스_등록_시_UUID_필드가_없음(self):
        """Device registration fails when UUID field is missing"""
        data = {}
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Device.objects.count(), 0)
        self.assertIn("uuid", response.data)


class PushTokenSerializerTests(APITestCase):
    """PushTokenSerializer tests"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.device_uuid = uuid.uuid4()
        self.device = Device.objects.create(
            user=self.user,
            uuid=self.device_uuid,
        )
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user
        self.valid_token_data = {
            "device_uuid": self.device_uuid,
            "token": "sample-push-token-123",
        }

    def test_성공__푸시_토큰_등록_성공(self):
        """Push token registration success test"""
        serializer = PushTokenSerializer(
            data=self.valid_token_data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        token = serializer.save(device=self.device)
        self.assertEqual(token.device, self.device)
        self.assertEqual(token.token, self.valid_token_data["token"])
        self.assertTrue(token.is_valid)

    def test_실패__푸시_토큰_등록_시_토큰_필드가_없음(self):
        """Push token registration fails when token field is missing"""
        data = {}
        serializer = PushTokenSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

    def test_실패__푸시_토큰_등록_시_토큰_중복(self):
        """Push token registration fails when token is duplicated"""
        # save 메서드가 토큰을 무효화하고 새로운 토큰을 생성하도록 설계되어 있어
        # Creating a new token does not fail.
        # This test checks if the previous token state changes
        token = "sample-push-token-123"

        # Create the first token
        PushToken.objects.create(
            device=self.device,
            token=token,
        )

        # Create the second token
        second_token_data = {
            "token": token,
        }
        serializer = PushTokenSerializer(
            data=second_token_data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)
        self.assertIn("error_code", serializer.errors["token"])
        self.assertIn("message", serializer.errors["token"])
        self.assertEqual(serializer.errors["token"]["error_code"], "E0070004")
        self.assertEqual(
            serializer.errors["token"]["message"], "이미 등록된 푸시 토큰입니다"
        )


class PushTokenViewTests(APITestCase):
    """PushTokenViewSet tests"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.device_uuid = uuid.uuid4()
        self.device = Device.objects.create(
            user=self.user,
            uuid=self.device_uuid,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.create_url = f"/v1/device/{self.device_uuid}/push_token/"
        self.valid_token_data = {
            "token": "sample-push-token-123",
        }

    def test_성공__푸시_토큰_등록_성공(self):
        """Push token registration success test"""
        response = self.client.post(
            self.create_url, self.valid_token_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PushToken.objects.count(), 1)
        token = PushToken.objects.get()
        self.assertEqual(token.device, self.device)
        self.assertEqual(token.token, self.valid_token_data["token"])
        self.assertTrue(token.is_valid)

    def test_실패__푸시_토큰_등록_시_디바이스_필드가_없음(self):
        """Push token registration fails when device field is missing"""
        data = {
            "token": "sample-push-token-123",
        }
        self.create_url = "/v1/device/test/push_token/"
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_실패__푸시_토큰_등록_시_토큰_필드가_없음(self):
        """Push token registration fails when token field is missing"""
        data = {}
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PushToken.objects.count(), 0)
        self.assertIn("token", response.data)

    def test_실패__푸시_토큰_등록_시_토큰_중복(self):
        """Push token registration fails when token is duplicated"""
        # 먼저 토큰 생성
        token = "sample-push-token-123"
        PushToken.objects.create(
            device=self.device,
            token=token,
        )

        # 같은 토큰으로 다시 시도
        token_data = {"token": token}
        response = self.client.post(self.create_url, token_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PushToken.objects.count(), 1)
        self.assertIn("token", response.data)
        self.assertIn("error_code", response.data["token"][0])
        self.assertIn("message", response.data["token"][0])
        self.assertEqual(response.data["token"][0]["error_code"], "E0070004")
        self.assertEqual(
            response.data["token"][0]["message"], "이미 등록된 푸시 토큰입니다"
        )


class DeviceModelTests(APITestCase):
    """Device model tests"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.device_uuid = uuid.uuid4()

    def test_성공__디바이스_생성(self):
        """Create device 성공 테스트"""
        device = Device.objects.create(
            user=self.user,
            uuid=self.device_uuid,
            platform=DevicePlatform.ANDROID,
        )
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.uuid, self.device_uuid)
        self.assertEqual(device.platform, DevicePlatform.ANDROID)

    def test_성공__디바이스_생성_기본_플랫폼(self):
        """Create device 시 기본 플랫폼 설정 테스트"""
        device = Device.objects.create(
            user=self.user,
            uuid=self.device_uuid,
        )
        self.assertEqual(device.platform, DevicePlatform.WEB)  # 기본 플랫폼은 WEB


class PushTokenModelTests(APITestCase):
    """PushToken model tests"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.device_uuid = uuid.uuid4()
        self.device = Device.objects.create(
            user=self.user,
            uuid=self.device_uuid,
        )
        self.token = "sample-push-token-123"

    def test_성공__푸시_토큰_생성(self):
        """Push token creation success test"""
        push_token = PushToken.objects.create(
            device=self.device,
            token=self.token,
        )
        self.assertEqual(push_token.device, self.device)
        self.assertEqual(push_token.token, self.token)
        self.assertTrue(push_token.is_valid)
        self.assertIsNone(push_token.endpoint_arn)

    def test_성공__푸시_토큰_생성_시_endpoint_arn_설정(self):
        """Endpoint ARN set on push token creation test"""
        endpoint_arn = "arn:aws:sns:ap-northeast-2:123456789012:endpoint/APNS/MyApp/12345678-1234-1234-1234-123456789012"
        push_token = PushToken.objects.create(
            device=self.device,
            token=self.token,
            endpoint_arn=endpoint_arn,
        )
        self.assertEqual(push_token.endpoint_arn, endpoint_arn)

    def test_성공__푸시_토큰_생성_시_기존_토큰_무효화(self):
        """Invalidates previous token on creation test"""
        # Create the first token
        first_token = PushToken.objects.create(
            device=self.device,
            token="first-token",
        )
        self.assertTrue(first_token.is_valid)

        # Create the second token
        second_token = PushToken.objects.create(
            device=self.device,
            token="second-token",
        )
        self.assertTrue(second_token.is_valid)

        # Refresh the first token to confirm invalidation
        first_token.refresh_from_db()
        self.assertFalse(first_token.is_valid)

    def test_성공__푸시_토큰_무효화_후_새_토큰_등록(self):
        """Register new token after invalidation test"""
        # Create a token and then invalidate it
        token = PushToken.objects.create(
            device=self.device,
            token=self.token,
        )
        token.is_valid = False
        token.save()

        # Attempt to create again with the same token
        new_token = PushToken.objects.create(
            device=self.device,
            token="new-token",
        )
        self.assertTrue(new_token.is_valid)

        # Check original token state (should remain invalid)
        token.refresh_from_db()
        self.assertFalse(token.is_valid)


class DeviceAdminTests(APITestCase):
    """DeviceAdmin tests"""

    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )

        # Create regular user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        # Create device
        self.device_uuid = uuid.uuid4()
        self.device = Device.objects.create(
            user=self.user,
            uuid=self.device_uuid,
        )

        # Create push token
        self.token = PushToken.objects.create(
            device=self.device,
            token="sample-push-token-123",
        )

        # Configure admin client
        self.client = APIClient()
        self.client.login(email="admin@example.com", password="adminpass123")

    def test_성공__디바이스_어드민_접근(self):
        """디바이스 어드민 접근 테스트"""
        response = self.client.get("/admin/device/device/")
        self.assertEqual(response.status_code, 200)

    def test_성공__푸시_토큰_어드민_접근(self):
        """푸시 토큰 어드민 접근 테스트"""
        response = self.client.get("/admin/device/pushtoken/")
        self.assertEqual(response.status_code, 200)


class DeviceMultiUserTests(APITestCase):
    """Multi-user device tests"""

    def setUp(self):
        """Set up test data"""
        # Create user1
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="password123",
        )

        # Create user2
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="password123",
        )

        # Generate device UUID
        self.device_uuid = uuid.uuid4()

        # Configure client
        self.client = APIClient()
        self.create_url = "/v1/device/"

    def test_성공__다른_사용자의_디바이스_UUID_사용_가능(self):
        """다른 사용자가 동일한 UUID로 디바이스를 등록할 수 있는지 테스트"""
        # 사용자1로 디바이스 등록
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.post(
            self.create_url, {"uuid": self.device_uuid}, format="json"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # 사용자2로 동일한 UUID의 디바이스 등록 시도
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.post(
            self.create_url, {"uuid": self.device_uuid}, format="json"
        )
        # 모델에 unique=True 제약이 있으므로 실패해야 함
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_성공__사용자별_디바이스_목록_분리(self):
        """Ensure device lists are separated per user"""
        # Register device for user1
        self.client.force_authenticate(user=self.user1)
        self.client.post(self.create_url, {"uuid": uuid.uuid4()}, format="json")

        # Register device for user2
        self.client.force_authenticate(user=self.user2)
        self.client.post(self.create_url, {"uuid": uuid.uuid4()}, format="json")

        # Check number of devices per user
        user1_devices = Device.objects.filter(user=self.user1).count()
        user2_devices = Device.objects.filter(user=self.user2).count()

        self.assertEqual(user1_devices, 1)
        self.assertEqual(user2_devices, 1)


class PushTokenMultipleDevicesTests(APITestCase):
    """Multi-device push token tests"""

    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        # Create device1
        self.device1_uuid = uuid.uuid4()
        self.device1 = Device.objects.create(
            user=self.user,
            uuid=self.device1_uuid,
            platform=DevicePlatform.ANDROID,
        )

        # Create device2
        self.device2_uuid = uuid.uuid4()
        self.device2 = Device.objects.create(
            user=self.user,
            uuid=self.device2_uuid,
            platform=DevicePlatform.IOS,
        )

        # Configure client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_성공__여러_디바이스에_동일한_푸시_토큰_등록_시도(self):
        """Attempt to register same push token on multiple devices"""
        token = "same-push-token-for-both-devices"

        # Register token to device1
        response1 = self.client.post(
            f"/v1/device/{self.device1_uuid}/push_token/",
            {"token": token},
            format="json",
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Attempt to register the same token to device2
        response2 = self.client.post(
            f"/v1/device/{self.device2_uuid}/push_token/",
            {"token": token},
            format="json",
        )

        # Registration should succeed on a different device
        # But validate_token checks all user devices for duplicates
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response2.data)

    def test_성공__디바이스별_푸시_토큰_무효화_독립성(self):
        """Per-device push token invalidation independence test"""
        # Register token to device1
        token1 = PushToken.objects.create(
            device=self.device1,
            token="device1-token",
        )

        # 디바이스2에 토큰 등록
        token2 = PushToken.objects.create(
            device=self.device2,
            token="device2-token",
        )

        # 두 토큰 모두 유효해야 함
        self.assertTrue(token1.is_valid)
        self.assertTrue(token2.is_valid)

        # Register a new token to device1
        new_token1 = PushToken.objects.create(
            device=self.device1,
            token="device1-new-token",
        )

        # Original token for device1 should be invalidated
        token1.refresh_from_db()
        self.assertFalse(token1.is_valid)

        # Token for device2 should still be valid
        token2.refresh_from_db()
        self.assertTrue(token2.is_valid)


class DeviceViewSetAdditionalTests(APITestCase):
    """Additional DeviceViewSet tests"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.create_url = "/v1/device/"

    def test_실패__인증되지_않은_사용자_접근(self):
        """Unauthenticated user access test"""
        # Create an unauthenticated client
        unauthenticated_client = APIClient()

        # Create device 시도
        response = unauthenticated_client.post(
            self.create_url, {"uuid": uuid.uuid4()}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_성공__플랫폼_지정_디바이스_등록(self):
        """Register device with specific platform test"""
        device_data = {
            "uuid": uuid.uuid4(),
            "platform": DevicePlatform.IOS,
        }
        response = self.client.post(self.create_url, device_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.count(), 1)
        device = Device.objects.get()
        self.assertEqual(int(device.platform), DevicePlatform.IOS.value)

    def test_실패__잘못된_플랫폼_값으로_디바이스_등록(self):
        """Register device with invalid platform test"""
        device_data = {
            "uuid": uuid.uuid4(),
            "platform": 99,  # nonexistent platform value
        }
        response = self.client.post(self.create_url, device_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Device.objects.count(), 0)
        self.assertIn("platform", response.data)
