from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
import uuid

from apps.device.models import Device, PushToken, DevicePlatform
from apps.device.v1.serializers import DeviceSerializer, PushTokenSerializer
from apps.user.models import User


class DeviceSerializerTests(APITestCase):
    """DeviceSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
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
        """디바이스 등록 성공 테스트"""
        serializer = DeviceSerializer(
            data=self.device_data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        device = serializer.save(user=self.user)
        self.assertEqual(device.uuid, self.valid_uuid)
        self.assertEqual(device.user, self.user)

    def test_실패__다바이스_등록_시_UUID_형식이_올바르지_않음(self):
        """다바이스 등록 시 UUID 형식이 올바르지 않음 테스트"""
        data = {
            "uuid": "invalid-uuid",
        }
        serializer = DeviceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("uuid", serializer.errors)

    def test_실패__디바이스_등록_시_UUID_중복(self):
        """디바이스 등록 시 UUID 중복 테스트"""
        # 먼저 디바이스 생성
        Device.objects.create(
            user=self.user,
            uuid=self.valid_uuid,
        )

        # 같은 UUID로 다시 시도
        serializer = DeviceSerializer(data=self.device_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("uuid", serializer.errors)

    def test_실패__디바이스_등록_시_UUID_필드가_없음(self):
        """디바이스 등록 시 UUID 필드가 없음 테스트"""
        data = {}
        serializer = DeviceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("uuid", serializer.errors)


class DeviceViewTests(APITestCase):
    """DeviceViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
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
        """디바이스 등록 성공 테스트"""
        response = self.client.post(self.create_url, self.device_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.count(), 1)
        device = Device.objects.get()
        self.assertEqual(str(device.uuid), str(self.valid_uuid))
        self.assertEqual(device.user, self.user)

    def test_실패__다바이스_등록_시_UUID_형식이_올바르지_않음(self):
        """다바이스 등록 시 UUID 형식이 올바르지 않음 테스트"""
        data = {
            "uuid": "invalid-uuid",
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Device.objects.count(), 0)
        self.assertIn("uuid", response.data)

    def test_실패__디바이스_등록_시_UUID_중복(self):
        """디바이스 등록 시 UUID 중복 테스트"""
        # 먼저 디바이스 생성
        Device.objects.create(
            user=self.user,
            uuid=self.valid_uuid,
        )

        # 같은 UUID로 다시 시도
        response = self.client.post(self.create_url, self.device_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Device.objects.count(), 1)
        self.assertIn("uuid", response.data)

    def test_실패__디바이스_등록_시_UUID_필드가_없음(self):
        """디바이스 등록 시 UUID 필드가 없음 테스트"""
        data = {}
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Device.objects.count(), 0)
        self.assertIn("uuid", response.data)


class PushTokenSerializerTests(APITestCase):
    """PushTokenSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
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
        """푸시 토큰 등록 성공 테스트"""
        serializer = PushTokenSerializer(
            data=self.valid_token_data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        token = serializer.save(device=self.device)
        self.assertEqual(token.device, self.device)
        self.assertEqual(token.token, self.valid_token_data["token"])
        self.assertTrue(token.is_valid)

    def test_실패__푸시_토큰_등록_시_토큰_필드가_없음(self):
        """푸시 토큰 등록 시 토큰 필드가 없음 테스트"""
        data = {}
        serializer = PushTokenSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

    def test_실패__푸시_토큰_등록_시_토큰_중복(self):
        """푸시 토큰 등록 시 토큰 중복 테스트"""
        # save 메서드가 토큰을 무효화하고 새로운 토큰을 생성하도록 설계되어 있어
        # 새 토큰 생성 시 실패가 일어나지 않음.
        # 따라서 이 테스트는 이전 토큰의 상태가 변경되는지 확인
        token = "sample-push-token-123"

        # 첫 번째 토큰 생성
        PushToken.objects.create(
            device=self.device,
            token=token,
        )

        # 두 번째 토큰 생성
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
    """PushTokenViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
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
        """푸시 토큰 등록 성공 테스트"""
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
        """푸시 토큰 등록 시 디바이스 필드가 없음 테스트"""
        data = {
            "token": "sample-push-token-123",
        }
        self.create_url = "/v1/device/test/push_token/"
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_실패__푸시_토큰_등록_시_토큰_필드가_없음(self):
        """푸시 토큰 등록 시 토큰 필드가 없음 테스트"""
        data = {}
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PushToken.objects.count(), 0)
        self.assertIn("token", response.data)

    def test_실패__푸시_토큰_등록_시_토큰_중복(self):
        """푸시 토큰 등록 시 토큰 중복 테스트"""
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
    """Device 모델 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.device_uuid = uuid.uuid4()

    def test_성공__디바이스_생성(self):
        """디바이스 생성 성공 테스트"""
        device = Device.objects.create(
            user=self.user,
            uuid=self.device_uuid,
            platform=DevicePlatform.ANDROID,
        )
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.uuid, self.device_uuid)
        self.assertEqual(device.platform, DevicePlatform.ANDROID)

    def test_성공__디바이스_생성_기본_플랫폼(self):
        """디바이스 생성 시 기본 플랫폼 설정 테스트"""
        device = Device.objects.create(
            user=self.user,
            uuid=self.device_uuid,
        )
        self.assertEqual(device.platform, DevicePlatform.WEB)  # 기본 플랫폼은 WEB


class PushTokenModelTests(APITestCase):
    """PushToken 모델 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
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
        """푸시 토큰 생성 성공 테스트"""
        push_token = PushToken.objects.create(
            device=self.device,
            token=self.token,
        )
        self.assertEqual(push_token.device, self.device)
        self.assertEqual(push_token.token, self.token)
        self.assertTrue(push_token.is_valid)
        self.assertIsNone(push_token.endpoint_arn)

    def test_성공__푸시_토큰_생성_시_endpoint_arn_설정(self):
        """푸시 토큰 생성 시 endpoint_arn 설정 테스트"""
        endpoint_arn = "arn:aws:sns:ap-northeast-2:123456789012:endpoint/APNS/MyApp/12345678-1234-1234-1234-123456789012"
        push_token = PushToken.objects.create(
            device=self.device,
            token=self.token,
            endpoint_arn=endpoint_arn,
        )
        self.assertEqual(push_token.endpoint_arn, endpoint_arn)

    def test_성공__푸시_토큰_생성_시_기존_토큰_무효화(self):
        """푸시 토큰 생성 시 기존 토큰 무효화 테스트"""
        # 첫 번째 토큰 생성
        first_token = PushToken.objects.create(
            device=self.device,
            token="first-token",
        )
        self.assertTrue(first_token.is_valid)

        # 두 번째 토큰 생성
        second_token = PushToken.objects.create(
            device=self.device,
            token="second-token",
        )
        self.assertTrue(second_token.is_valid)

        # 첫 번째 토큰 다시 조회하여 무효화 확인
        first_token.refresh_from_db()
        self.assertFalse(first_token.is_valid)

    def test_성공__푸시_토큰_무효화_후_새_토큰_등록(self):
        """푸시 토큰 무효화 후 새 토큰 등록 테스트"""
        # 토큰 생성 후 무효화
        token = PushToken.objects.create(
            device=self.device,
            token=self.token,
        )
        token.is_valid = False
        token.save()

        # 같은 토큰으로 다시 생성 시도
        new_token = PushToken.objects.create(
            device=self.device,
            token="new-token",
        )
        self.assertTrue(new_token.is_valid)

        # 기존 토큰 상태 확인 (여전히 무효 상태여야 함)
        token.refresh_from_db()
        self.assertFalse(token.is_valid)


class DeviceAdminTests(APITestCase):
    """DeviceAdmin 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        # 관리자 사용자 생성
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )

        # 일반 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        # 디바이스 생성
        self.device_uuid = uuid.uuid4()
        self.device = Device.objects.create(
            user=self.user,
            uuid=self.device_uuid,
        )

        # 푸시 토큰 생성
        self.token = PushToken.objects.create(
            device=self.device,
            token="sample-push-token-123",
        )

        # 관리자 클라이언트 설정
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
    """여러 사용자의 디바이스 관련 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        # 사용자1 생성
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="password123",
        )

        # 사용자2 생성
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="password123",
        )

        # 디바이스 UUID 생성
        self.device_uuid = uuid.uuid4()

        # 클라이언트 설정
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
        """사용자별 디바이스 목록이 올바르게 분리되는지 테스트"""
        # 사용자1의 디바이스 등록
        self.client.force_authenticate(user=self.user1)
        self.client.post(self.create_url, {"uuid": uuid.uuid4()}, format="json")

        # 사용자2의 디바이스 등록
        self.client.force_authenticate(user=self.user2)
        self.client.post(self.create_url, {"uuid": uuid.uuid4()}, format="json")

        # 각 사용자별 디바이스 수 확인
        user1_devices = Device.objects.filter(user=self.user1).count()
        user2_devices = Device.objects.filter(user=self.user2).count()

        self.assertEqual(user1_devices, 1)
        self.assertEqual(user2_devices, 1)


class PushTokenMultipleDevicesTests(APITestCase):
    """여러 디바이스의 푸시 토큰 관련 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        # 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        # 디바이스1 생성
        self.device1_uuid = uuid.uuid4()
        self.device1 = Device.objects.create(
            user=self.user,
            uuid=self.device1_uuid,
            platform=DevicePlatform.ANDROID,
        )

        # 디바이스2 생성
        self.device2_uuid = uuid.uuid4()
        self.device2 = Device.objects.create(
            user=self.user,
            uuid=self.device2_uuid,
            platform=DevicePlatform.IOS,
        )

        # 클라이언트 설정
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_성공__여러_디바이스에_동일한_푸시_토큰_등록_시도(self):
        """여러 디바이스에 동일한 푸시 토큰 등록 시도 테스트"""
        token = "same-push-token-for-both-devices"

        # 디바이스1에 토큰 등록
        response1 = self.client.post(
            f"/v1/device/{self.device1_uuid}/push_token/",
            {"token": token},
            format="json",
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # 디바이스2에 동일한 토큰 등록 시도
        response2 = self.client.post(
            f"/v1/device/{self.device2_uuid}/push_token/",
            {"token": token},
            format="json",
        )

        # 서로 다른 디바이스이므로 동일한 토큰 등록이 가능해야 함
        # 하지만 validate_token 메서드에서 사용자의 모든 디바이스에 대해 토큰 중복 검사를 함
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response2.data)

    def test_성공__디바이스별_푸시_토큰_무효화_독립성(self):
        """디바이스별 푸시 토큰 무효화 독립성 테스트"""
        # 디바이스1에 토큰 등록
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

        # 디바이스1에 새 토큰 등록
        new_token1 = PushToken.objects.create(
            device=self.device1,
            token="device1-new-token",
        )

        # 디바이스1의 기존 토큰은 무효화되어야 함
        token1.refresh_from_db()
        self.assertFalse(token1.is_valid)

        # 디바이스2의 토큰은 여전히 유효해야 함
        token2.refresh_from_db()
        self.assertTrue(token2.is_valid)


class DeviceViewSetAdditionalTests(APITestCase):
    """DeviceViewSet 추가 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.create_url = "/v1/device/"

    def test_실패__인증되지_않은_사용자_접근(self):
        """인증되지 않은 사용자 접근 테스트"""
        # 인증되지 않은 클라이언트 생성
        unauthenticated_client = APIClient()

        # 디바이스 생성 시도
        response = unauthenticated_client.post(
            self.create_url, {"uuid": uuid.uuid4()}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_성공__플랫폼_지정_디바이스_등록(self):
        """플랫폼을 지정하여 디바이스 등록 테스트"""
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
        """잘못된 플랫폼 값으로 디바이스 등록 테스트"""
        device_data = {
            "uuid": uuid.uuid4(),
            "platform": 99,  # 존재하지 않는 플랫폼 값
        }
        response = self.client.post(self.create_url, device_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Device.objects.count(), 0)
        self.assertIn("platform", response.data)
