from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.cms.admin import (
    NoticeAdmin,
    EventAdmin,
    FaqAdmin,
    make_published,
    make_unpublished,
)
from apps.cms.models import Notice, Event, Faq, FaqCategory
from apps.cms.v1.filters import NoticeFilterSet, EventFilterSet, FaqFilterSet
from apps.cms.v1.serializers import (
    NoticeSerializer,
    EventSerializer,
    FaqSerializer,
    FaqCategorySerializer,
)
from apps.user.models import User


class NoticeSerializerTests(APITestCase):
    """NoticeSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        now = timezone.now()
        self.notice = Notice.objects.create(
            author=self.user,
            title="테스트 공지사항",
            content="테스트 공지사항 내용입니다.",
            published_at=now,
            start_at=now,
            end_at=now + timedelta(days=7),
            is_published=True,
        )

    def test_성공__공지사항_정보가_올바르게_직렬화(self):
        """공지사항 정보가 올바르게 직렬화되는지 테스트"""
        serializer = NoticeSerializer(self.notice)
        data = serializer.data

        self.assertEqual(str(data["uuid"]), str(self.notice.uuid))
        self.assertEqual(data["title"], self.notice.title)
        self.assertEqual(data["content"], self.notice.content)

        # 시간 포맷이 ISO 8601 형식인지만 확인하고 정확한 값은 비교하지 않음
        self.assertIn(
            "T", data["start_at"]
        )  # ISO 8601 형식은 날짜와 시간 사이에 'T'가 있음
        self.assertIn("T", data["end_at"])


class EventSerializerTests(APITestCase):
    """EventSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        now = timezone.now()
        self.event = Event.objects.create(
            author=self.user,
            title="테스트 이벤트",
            content="테스트 이벤트 내용입니다.",
            published_at=now,
            start_at=now,
            end_at=now + timedelta(days=14),
            event_start_at=now + timedelta(days=1),
            event_end_at=now + timedelta(days=10),
            is_published=True,
        )

    def test_성공__이벤트_정보가_올바르게_직렬화(self):
        """이벤트 정보가 올바르게 직렬화되는지 테스트"""
        serializer = EventSerializer(self.event)
        data = serializer.data

        self.assertEqual(str(data["uuid"]), str(self.event.uuid))
        self.assertEqual(data["title"], self.event.title)
        self.assertEqual(data["content"], self.event.content)

        # 시간 포맷이 ISO 8601 형식인지만 확인하고 정확한 값은 비교하지 않음
        self.assertIn("T", data["start_at"])
        self.assertIn("T", data["end_at"])
        self.assertIn("T", data["event_start_at"])
        self.assertIn("T", data["event_end_at"])

    def test_성공__이벤트_종료_여부_확인(self):
        """이벤트 종료 여부가 올바르게 확인되는지 테스트"""
        # 이벤트가 진행 중인 경우 (종료일이 미래)
        now = timezone.now()
        self.event.event_end_at = now + timedelta(
            days=7
        )  # 이벤트 종료일을 명확하게 미래로 설정
        self.event.save()

        serializer = EventSerializer(self.event)
        self.assertFalse(serializer.data["is_event_ended"])

        # 이벤트가 종료된 경우 (종료일이 과거)
        self.event.event_end_at = now - timedelta(
            days=1
        )  # 이벤트 종료 일시를 과거로 설정
        self.event.save()

        serializer = EventSerializer(self.event)
        self.assertTrue(serializer.data["is_event_ended"])


class FaqCategorySerializerTests(APITestCase):
    """FaqCategorySerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.category = FaqCategory.objects.create(
            name="테스트 카테고리",
        )

    def test_성공__FAQ_카테고리_정보가_올바르게_직렬화(self):
        """FAQ 카테고리 정보가 올바르게 직렬화되는지 테스트"""
        serializer = FaqCategorySerializer(self.category)
        data = serializer.data

        self.assertEqual(str(data["uuid"]), str(self.category.uuid))
        self.assertEqual(data["name"], self.category.name)


class FaqSerializerTests(APITestCase):
    """FaqSerializer 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        self.category = FaqCategory.objects.create(
            name="테스트 카테고리",
        )

        now = timezone.now()
        self.faq = Faq.objects.create(
            author=self.user,
            category=self.category,
            title="테스트 FAQ",
            content="테스트 FAQ 내용입니다.",
            published_at=now,
            is_published=True,
        )

    def test_성공__FAQ_정보가_올바르게_직렬화(self):
        """FAQ 정보가 올바르게 직렬화되는지 테스트"""
        serializer = FaqSerializer(self.faq)
        data = serializer.data

        self.assertEqual(str(data["uuid"]), str(self.faq.uuid))
        self.assertEqual(data["title"], self.faq.title)
        self.assertEqual(data["content"], self.faq.content)
        self.assertEqual(str(data["category"]["uuid"]), str(self.category.uuid))
        self.assertEqual(data["category"]["name"], self.category.name)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class NoticeViewSetTests(APITestCase):
    """NoticeViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        now = timezone.now()

        # 활성화된 공지사항 (현재 기간 내)
        self.active_notice = Notice.objects.create(
            author=self.user,
            title="활성화된 공지사항",
            content="활성화된 공지사항 내용입니다.",
            published_at=now - timedelta(days=1),
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=7),
            is_published=True,
        )

        # 미래 시작일 공지사항
        self.future_notice = Notice.objects.create(
            author=self.user,
            title="미래 공지사항",
            content="미래 공지사항 내용입니다.",
            published_at=now,
            start_at=now + timedelta(days=1),
            end_at=now + timedelta(days=8),
            is_published=True,
        )

        # 종료된 공지사항
        self.ended_notice = Notice.objects.create(
            author=self.user,
            title="종료된 공지사항",
            content="종료된 공지사항 내용입니다.",
            published_at=now - timedelta(days=10),
            start_at=now - timedelta(days=10),
            end_at=now - timedelta(days=1),
            is_published=True,
        )

        # 미발행 공지사항
        self.unpublished_notice = Notice.objects.create(
            author=self.user,
            title="미발행 공지사항",
            content="미발행 공지사항 내용입니다.",
            published_at=now,
            start_at=now,
            end_at=now + timedelta(days=7),
            is_published=False,
        )

        # API 경로
        self.notice_list_url = "/v1/cms/notice/"
        self.notice_detail_url = f"/v1/cms/notice/{self.active_notice.uuid}/"

    def test_성공__활성화된_공지사항_목록_조회(self):
        """활성화된 공지사항 목록 조회 성공 테스트"""
        response = self.client.get(self.notice_list_url + "?limit=10&offset=0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회된 공지사항 수가 기대한 값과 일치하는지 확인 (활성화된 공지사항만)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["uuid"], str(self.active_notice.uuid)
        )

        # 미래 공지사항, 종료된 공지사항, 미발행 공지사항은 포함되지 않는지 확인
        uuids = [item["uuid"] for item in response.data["results"]]
        self.assertNotIn(str(self.future_notice.uuid), uuids)
        self.assertNotIn(str(self.ended_notice.uuid), uuids)
        self.assertNotIn(str(self.unpublished_notice.uuid), uuids)

    def test_성공__공지사항_상세_조회(self):
        """공지사항 상세 조회 성공 테스트"""
        response = self.client.get(self.notice_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["uuid"], str(self.active_notice.uuid))
        self.assertEqual(response.data["title"], self.active_notice.title)
        self.assertEqual(response.data["content"], self.active_notice.content)

    def test_실패__미인증_사용자_접근_거부(self):
        """미인증 사용자 접근 거부 테스트"""
        # 클라이언트에서 인증 정보 제거
        self.client.force_authenticate(user=None)

        response = self.client.get(self.notice_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.notice_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_실패__사용자_수정_거부(self):
        """사용자의 공지사항 수정 요청 거부 테스트"""
        data = {"title": "수정된 제목"}

        response = self.client.patch(self.notice_detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.put(self.notice_detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.post(self.notice_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.delete(self.notice_detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_성공__제목으로_공지사항_필터링(self):
        """제목으로 공지사항 필터링 성공 테스트"""
        # 제목에 '활성화' 포함된 공지사항 필터링
        response = self.client.get(
            f"{self.notice_list_url}?title__icontains=활성화&limit=10&offset=0"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["uuid"], str(self.active_notice.uuid)
        )

        # 제목에 '존재하지 않는' 포함된 공지사항 필터링 (결과 없음)
        response = self.client.get(
            f"{self.notice_list_url}?title__icontains=존재하지 않는&limit=10&offset=0"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class EventViewSetTests(APITestCase):
    """EventViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        now = timezone.now()

        # 활성화된 이벤트 (현재 기간 내)
        self.active_event = Event.objects.create(
            author=self.user,
            title="활성화된 이벤트",
            content="활성화된 이벤트 내용입니다.",
            published_at=now - timedelta(days=1),
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=7),
            event_start_at=now,
            event_end_at=now + timedelta(days=5),
            is_published=True,
        )

        # 미래 시작일 이벤트
        self.future_event = Event.objects.create(
            author=self.user,
            title="미래 이벤트",
            content="미래 이벤트 내용입니다.",
            published_at=now,
            start_at=now + timedelta(days=1),
            end_at=now + timedelta(days=8),
            event_start_at=now + timedelta(days=2),
            event_end_at=now + timedelta(days=7),
            is_published=True,
        )

        # 종료된 이벤트
        self.ended_event = Event.objects.create(
            author=self.user,
            title="종료된 이벤트",
            content="종료된 이벤트 내용입니다.",
            published_at=now - timedelta(days=10),
            start_at=now - timedelta(days=10),
            end_at=now - timedelta(days=1),
            event_start_at=now - timedelta(days=9),
            event_end_at=now - timedelta(days=2),
            is_published=True,
        )

        # 미발행 이벤트
        self.unpublished_event = Event.objects.create(
            author=self.user,
            title="미발행 이벤트",
            content="미발행 이벤트 내용입니다.",
            published_at=now,
            start_at=now,
            end_at=now + timedelta(days=7),
            event_start_at=now + timedelta(days=1),
            event_end_at=now + timedelta(days=6),
            is_published=False,
        )

        # API 경로
        self.event_list_url = "/v1/cms/event/"
        self.event_detail_url = f"/v1/cms/event/{self.active_event.uuid}/"

    def test_성공__활성화된_이벤트_목록_조회(self):
        """활성화된 이벤트 목록 조회 성공 테스트"""
        response = self.client.get(self.event_list_url + "?limit=10&offset=0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회된 이벤트 수가 기대한 값과 일치하는지 확인 (활성화된 이벤트만)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["uuid"], str(self.active_event.uuid)
        )

        # 미래 이벤트, 종료된 이벤트, 미발행 이벤트는 포함되지 않는지 확인
        uuids = [item["uuid"] for item in response.data["results"]]
        self.assertNotIn(str(self.future_event.uuid), uuids)
        self.assertNotIn(str(self.ended_event.uuid), uuids)
        self.assertNotIn(str(self.unpublished_event.uuid), uuids)

    def test_성공__이벤트_상세_조회(self):
        """이벤트 상세 조회 성공 테스트"""
        response = self.client.get(self.event_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["uuid"], str(self.active_event.uuid))
        self.assertEqual(response.data["title"], self.active_event.title)
        self.assertEqual(response.data["content"], self.active_event.content)
        self.assertFalse(
            response.data["is_event_ended"]
        )  # 활성 이벤트는 종료되지 않았음

    def test_실패__미인증_사용자_접근_거부(self):
        """미인증 사용자 접근 거부 테스트"""
        # 클라이언트에서 인증 정보 제거
        self.client.force_authenticate(user=None)

        response = self.client.get(self.event_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.event_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_성공__제목으로_이벤트_필터링(self):
        """제목으로 이벤트 필터링 성공 테스트"""
        # 제목에 '활성화' 포함된 이벤트 필터링
        response = self.client.get(
            f"{self.event_list_url}?title__icontains=활성화&limit=10&offset=0"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["uuid"], str(self.active_event.uuid)
        )

        # 제목에 '존재하지 않는' 포함된 이벤트 필터링 (결과 없음)
        response = self.client.get(
            f"{self.event_list_url}?title__icontains=존재하지 않는&limit=10&offset=0"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class FaqViewSetTests(APITestCase):
    """FaqViewSet 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        # 캐시 무효화
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        now = timezone.now()

        # FAQ 카테고리 생성
        self.category1 = FaqCategory.objects.create(name="일반")
        self.category2 = FaqCategory.objects.create(name="계정")
        self.category3 = FaqCategory.objects.create(name="결제")

        # 발행된 FAQ들
        self.faq1 = Faq.objects.create(
            author=self.user,
            category=self.category1,
            title="일반 FAQ 1",
            content="일반 FAQ 1 내용입니다.",
            published_at=now - timedelta(days=5),
            is_published=True,
        )

        self.faq2 = Faq.objects.create(
            author=self.user,
            category=self.category2,
            title="계정 관련 FAQ",
            content="계정 관련 FAQ 내용입니다.",
            published_at=now - timedelta(days=3),
            is_published=True,
        )

        # 미발행 FAQ
        self.unpublished_faq = Faq.objects.create(
            author=self.user,
            category=self.category3,
            title="결제 관련 FAQ",
            content="결제 관련 FAQ 내용입니다.",
            published_at=now,
            is_published=False,
        )

        # API 경로
        self.faq_list_url = "/v1/cms/faq/"

    def test_성공__발행된_FAQ_목록_조회(self):
        """발행된 FAQ 목록 조회 성공 테스트"""
        response = self.client.get(self.faq_list_url + "?limit=10&offset=0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회된 FAQ 수가 기대한 값과 일치하는지 확인 (발행된 FAQ만)
        self.assertEqual(len(response.data["results"]), 2)

        # 미발행 FAQ는 포함되지 않는지 확인
        uuids = [item["uuid"] for item in response.data["results"]]
        self.assertNotIn(str(self.unpublished_faq.uuid), uuids)

    def test_실패__미인증_사용자_접근_거부(self):
        """미인증 사용자 접근 거부 테스트"""
        # 클라이언트에서 인증 정보 제거
        self.client.force_authenticate(user=None)

        response = self.client.get(self.faq_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_성공__카테고리로_FAQ_필터링(self):
        """카테고리로 FAQ 필터링 성공 테스트"""
        # '일반' 카테고리 FAQ 필터링
        response = self.client.get(
            f"{self.faq_list_url}?category_name=일반&limit=10&offset=0"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["uuid"], str(self.faq1.uuid))

        # '계정' 카테고리 FAQ 필터링
        response = self.client.get(
            f"{self.faq_list_url}?category_name=계정&limit=10&offset=0"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["uuid"], str(self.faq2.uuid))

        # 존재하지 않는 카테고리 필터링 (결과 없음)
        response = self.client.get(
            f"{self.faq_list_url}?category_name=존재하지 않음&limit=10&offset=0"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_실패__FAQ_상세_조회_지원하지_않음(self):
        """FAQ 상세 조회가 지원되지 않는지 테스트"""
        # FAQ 뷰셋은 ListModelMixin만 상속받았으므로 상세 조회를 지원하지 않음
        response = self.client.get(f"{self.faq_list_url}{self.faq1.uuid}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FilterTests(APITestCase):
    """필터셋 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        now = timezone.now()

        # Notice 객체 생성
        self.notice1 = Notice.objects.create(
            author=self.user,
            title="공지사항 1",
            content="공지사항 1 내용",
            published_at=now - timedelta(days=2),
            start_at=now - timedelta(days=2),
            end_at=now + timedelta(days=5),
            is_published=True,
        )

        self.notice2 = Notice.objects.create(
            author=self.user,
            title="중요 공지사항",
            content="중요 공지사항 내용",
            published_at=now - timedelta(days=1),
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=6),
            is_published=True,
        )

        # Event 객체 생성
        self.event1 = Event.objects.create(
            author=self.user,
            title="이벤트 1",
            content="이벤트 1 내용",
            published_at=now - timedelta(days=2),
            start_at=now - timedelta(days=2),
            end_at=now + timedelta(days=5),
            event_start_at=now,
            event_end_at=now + timedelta(days=3),
            is_published=True,
        )

        self.event2 = Event.objects.create(
            author=self.user,
            title="특별 이벤트",
            content="특별 이벤트 내용",
            published_at=now - timedelta(days=1),
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=6),
            event_start_at=now + timedelta(days=1),
            event_end_at=now + timedelta(days=4),
            is_published=True,
        )

        # FAQ 카테고리 생성
        self.category1 = FaqCategory.objects.create(name="일반")
        self.category2 = FaqCategory.objects.create(name="계정")

        # FAQ 객체 생성
        self.faq1 = Faq.objects.create(
            author=self.user,
            category=self.category1,
            title="FAQ 1",
            content="FAQ 1 내용",
            published_at=now - timedelta(days=2),
            is_published=True,
        )

        self.faq2 = Faq.objects.create(
            author=self.user,
            category=self.category2,
            title="FAQ 2",
            content="FAQ 2 내용",
            published_at=now - timedelta(days=1),
            is_published=True,
        )

    def test_성공__공지사항_제목_필터링(self):
        """공지사항 제목으로 필터링 성공 테스트"""
        # 필터셋 인스턴스 생성
        filterset = NoticeFilterSet(
            {"title__icontains": "중요"}, queryset=Notice.objects.all()
        )

        # 필터링된 결과 확인
        self.assertEqual(len(filterset.qs), 1)
        self.assertEqual(filterset.qs[0].title, "중요 공지사항")

    def test_성공__이벤트_제목_필터링(self):
        """이벤트 제목으로 필터링 성공 테스트"""
        # 필터셋 인스턴스 생성
        filterset = EventFilterSet(
            {"title__icontains": "특별"}, queryset=Event.objects.all()
        )

        # 필터링된 결과 확인
        self.assertEqual(len(filterset.qs), 1)
        self.assertEqual(filterset.qs[0].title, "특별 이벤트")

    def test_성공__FAQ_카테고리_필터링(self):
        """FAQ 카테고리로 필터링 성공 테스트"""
        # 필터셋 인스턴스 생성
        filterset = FaqFilterSet({"category_name": "계정"}, queryset=Faq.objects.all())

        # 필터링된 결과 확인
        self.assertEqual(len(filterset.qs), 1)
        self.assertEqual(filterset.qs[0].title, "FAQ 2")
        self.assertEqual(filterset.qs[0].category.name, "계정")


class AdminActionTests(APITestCase):
    """어드민 액션 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            is_staff=True,
            is_superuser=True,
        )

        self.site = AdminSite()
        self.now = timezone.now()

        # 공지사항 객체 생성
        self.notice = Notice.objects.create(
            author=self.user,
            title="미발행 공지사항",
            content="미발행 공지사항 내용",
            published_at=self.now,
            start_at=self.now,
            end_at=self.now + timedelta(days=7),
            is_published=False,
        )

        # 이벤트 객체 생성
        self.event = Event.objects.create(
            author=self.user,
            title="미발행 이벤트",
            content="미발행 이벤트 내용",
            published_at=self.now,
            start_at=self.now,
            end_at=self.now + timedelta(days=7),
            event_start_at=self.now + timedelta(days=1),
            event_end_at=self.now + timedelta(days=5),
            is_published=False,
        )

        # FAQ 카테고리 생성
        self.category = FaqCategory.objects.create(name="테스트 카테고리")

        # FAQ 객체 생성
        self.faq = Faq.objects.create(
            author=self.user,
            category=self.category,
            title="미발행 FAQ",
            content="미발행 FAQ 내용",
            published_at=self.now,
            is_published=False,
        )

        # 어드민 모델 인스턴스 생성
        self.notice_admin = NoticeAdmin(Notice, self.site)
        self.event_admin = EventAdmin(Event, self.site)
        self.faq_admin = FaqAdmin(Faq, self.site)

    def test_성공__공지사항_발행_상태로_변경(self):
        """공지사항 발행 상태로 변경 성공 테스트"""
        # 액션 실행
        make_published(
            self.notice_admin, None, Notice.objects.filter(pk=self.notice.pk)
        )

        # 변경 사항 확인
        updated_notice = Notice.objects.get(pk=self.notice.pk)
        self.assertTrue(updated_notice.is_published)

    def test_성공__공지사항_미발행_상태로_변경(self):
        """공지사항 미발행 상태로 변경 성공 테스트"""
        # 먼저 발행 상태로 변경
        self.notice.is_published = True
        self.notice.save()

        # 액션 실행
        make_unpublished(
            self.notice_admin, None, Notice.objects.filter(pk=self.notice.pk)
        )

        # 변경 사항 확인
        updated_notice = Notice.objects.get(pk=self.notice.pk)
        self.assertFalse(updated_notice.is_published)

    def test_성공__FAQ_발행_상태로_변경(self):
        """FAQ 발행 상태로 변경 성공 테스트"""
        # 액션 실행
        make_published(self.faq_admin, None, Faq.objects.filter(pk=self.faq.pk))

        # 변경 사항 확인
        updated_faq = Faq.objects.get(pk=self.faq.pk)
        self.assertTrue(updated_faq.is_published)


class ModelTests(APITestCase):
    """모델 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.now = timezone.now()

    def test_성공__Notice_모델_생성(self):
        """Notice 모델 생성 성공 테스트"""
        notice = Notice.objects.create(
            author=self.user,
            title="테스트 공지사항",
            content="테스트 공지사항 내용",
            published_at=self.now,
            start_at=self.now,
            end_at=self.now + timedelta(days=7),
            is_published=True,
        )

        self.assertEqual(notice.title, "테스트 공지사항")
        self.assertEqual(notice.content, "테스트 공지사항 내용")
        self.assertEqual(notice.author, self.user)
        self.assertTrue(notice.is_published)
        self.assertIsNotNone(notice.uuid)

    def test_성공__Event_모델_생성(self):
        """Event 모델 생성 성공 테스트"""
        event = Event.objects.create(
            author=self.user,
            title="테스트 이벤트",
            content="테스트 이벤트 내용",
            published_at=self.now,
            start_at=self.now,
            end_at=self.now + timedelta(days=7),
            event_start_at=self.now + timedelta(days=1),
            event_end_at=self.now + timedelta(days=5),
            is_published=True,
        )

        self.assertEqual(event.title, "테스트 이벤트")
        self.assertEqual(event.content, "테스트 이벤트 내용")
        self.assertEqual(event.author, self.user)
        self.assertTrue(event.is_published)
        self.assertIsNotNone(event.uuid)

    def test_성공__FaqCategory_모델_생성(self):
        """FaqCategory 모델 생성 성공 테스트"""
        category = FaqCategory.objects.create(
            name="테스트 카테고리",
        )

        self.assertEqual(category.name, "테스트 카테고리")
        self.assertIsNotNone(category.uuid)

    def test_성공__Faq_모델_생성(self):
        """Faq 모델 생성 성공 테스트"""
        category = FaqCategory.objects.create(
            name="테스트 카테고리",
        )

        faq = Faq.objects.create(
            author=self.user,
            category=category,
            title="테스트 FAQ",
            content="테스트 FAQ 내용",
            published_at=self.now,
            is_published=True,
        )

        self.assertEqual(faq.title, "테스트 FAQ")
        self.assertEqual(faq.content, "테스트 FAQ 내용")
        self.assertEqual(faq.author, self.user)
        self.assertEqual(faq.category, category)
        self.assertTrue(faq.is_published)
        self.assertIsNotNone(faq.uuid)


class FaqCategoryViewSetTests(APITestCase):
    """FaqCategory에 대한 추가 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # FAQ 카테고리 생성
        self.category1 = FaqCategory.objects.create(name="일반")
        self.category2 = FaqCategory.objects.create(name="계정")
        self.category3 = FaqCategory.objects.create(name="결제")

        # 각 카테고리에 FAQ 추가
        now = timezone.now()

        # 일반 카테고리 FAQ
        self.faq1 = Faq.objects.create(
            author=self.user,
            category=self.category1,
            title="일반 FAQ 1",
            content="일반 FAQ 1 내용",
            published_at=now,
            is_published=True,
        )

        self.faq2 = Faq.objects.create(
            author=self.user,
            category=self.category1,
            title="일반 FAQ 2",
            content="일반 FAQ 2 내용",
            published_at=now,
            is_published=True,
        )

        # 계정 카테고리 FAQ
        self.faq3 = Faq.objects.create(
            author=self.user,
            category=self.category2,
            title="계정 FAQ",
            content="계정 FAQ 내용",
            published_at=now,
            is_published=True,
        )

        # 결제 카테고리 FAQ (미발행)
        self.faq4 = Faq.objects.create(
            author=self.user,
            category=self.category3,
            title="결제 FAQ",
            content="결제 FAQ 내용",
            published_at=now,
            is_published=False,
        )

        # URL
        self.faq_list_url = "/v1/cms/faq/"

    def test_성공__특정_카테고리_FAQ_조회(self):
        """특정 카테고리의 FAQ만 조회 성공 테스트"""
        # '일반' 카테고리의 FAQ 조회
        response = self.client.get(
            f"{self.faq_list_url}?category_name=일반&limit=10&offset=0"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회된 FAQ 수 확인
        self.assertEqual(len(response.data["results"]), 2)

        # 조회된 FAQ의 카테고리가 모두 '일반'인지 확인
        for item in response.data["results"]:
            self.assertEqual(item["category"]["name"], "일반")


class EdgeCaseTests(APITestCase):
    """엣지 케이스 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.now = timezone.now()

        # 특수 문자가 포함된 제목의 공지사항
        self.special_notice = Notice.objects.create(
            author=self.user,
            title="특수문자 테스트!@#$%^&*()",
            content="특수문자 테스트 내용",
            published_at=self.now,
            start_at=self.now,
            end_at=self.now + timedelta(days=7),
            is_published=True,
        )

        # 매우 긴 제목의 이벤트
        long_title = "매우 긴 제목" * 20  # 180자
        self.long_title_event = Event.objects.create(
            author=self.user,
            title=long_title,
            content="긴 제목 테스트 내용",
            published_at=self.now,
            start_at=self.now,
            end_at=self.now + timedelta(days=7),
            event_start_at=self.now,
            event_end_at=self.now + timedelta(days=5),
            is_published=True,
        )

        # 동일한 이름의 FAQ 카테고리 생성 시도
        self.category1 = FaqCategory.objects.create(name="중복 카테고리")

        # URL
        self.notice_detail_url = f"/v1/cms/notice/{self.special_notice.uuid}/"
        self.event_detail_url = f"/v1/cms/event/{self.long_title_event.uuid}/"

    def test_성공__특수문자_포함_공지사항_조회(self):
        """특수문자가 포함된 공지사항 조회 성공 테스트"""
        response = self.client.get(self.notice_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "특수문자 테스트!@#$%^&*()")

    def test_성공__매우_긴_제목_이벤트_조회(self):
        """매우 긴 제목의 이벤트 조회 성공 테스트"""
        response = self.client.get(self.event_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.long_title_event.title)

    def test_성공__동일_명칭_FAQ_카테고리_생성(self):
        """동일한 이름의 FAQ 카테고리 생성 테스트"""
        # 동일한 이름의 카테고리 생성은 허용됨 (제약 조건 없음)
        category2 = FaqCategory.objects.create(name="중복 카테고리")

        # 두 카테고리는 서로 다른 객체여야 함
        self.assertNotEqual(self.category1.uuid, category2.uuid)

        # 두 카테고리 이름은 동일해야 함
        self.assertEqual(self.category1.name, category2.name)

    def test_성공__없는_공지사항_조회(self):
        """존재하지 않는 공지사항 조회 테스트"""
        non_existent_uuid = "12345678-1234-1234-1234-123456789012"
        response = self.client.get(f"/v1/cms/notice/{non_existent_uuid}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_성공__과거_종료된_이벤트_직접_조회(self):
        """과거에 종료된 이벤트 직접 조회 테스트"""
        # 과거에 종료된 이벤트 생성
        past_event = Event.objects.create(
            author=self.user,
            title="과거 이벤트",
            content="과거 이벤트 내용",
            published_at=self.now - timedelta(days=20),
            start_at=self.now - timedelta(days=20),
            end_at=self.now - timedelta(days=10),
            event_start_at=self.now - timedelta(days=19),
            event_end_at=self.now - timedelta(days=11),
            is_published=True,
        )

        # 목록에서는 조회되지 않아야 함
        response = self.client.get("/v1/cms/event/?limit=10&offset=0")
        uuids = [item["uuid"] for item in response.data["results"]]
        self.assertNotIn(str(past_event.uuid), uuids)
