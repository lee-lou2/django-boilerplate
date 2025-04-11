import datetime
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.feed.models import (
    Feed,
    FeedComment,
    FeedTag,
    FeedLike,
    FeedReport,
    FeedReportReason,
    FeedCommentLike,
    FeedCommentReport,
)
from apps.feed.v1.fields import CurrentFeedDefault
from apps.feed.v1.serializers import (
    FeedSerializer,
    FeedLikeSerializer,
    FeedReportSerializer,
    FeedCommentSerializer,
    FeedCommentLikeSerializer,
    FeedCommentReportSerializer,
    FeedListSerializer,
    FeedRetrieveSerializer,
)
from apps.feed.v1.views import FeedCommentViewSet
from apps.user.models import User, UserProfile
from common.enums.errors import (
    E006_FEED_ALREADY_REPORTED,
    E006_COMMENT_ALREADY_REPORTED,
)


class FeedSerializerTest(TestCase):
    """피드 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 현재 시간
        self.now = timezone.now()

        # 유효한 피드 데이터
        self.valid_data = {
            "title": "테스트 피드",
            "content": "피드 내용입니다.",
            "image": "https://example.com/image.jpg",
            "tags": [{"name": "태그1"}, {"name": "태그2"}],
            "published_at": self.now.isoformat(),
        }

    def test_성공__피드_생성(self):
        """테스트: 피드 생성 성공"""
        serializer = FeedSerializer(
            data=self.valid_data,
            context={"request": type("obj", (object,), {"user": self.user})},
        )

        self.assertTrue(serializer.is_valid())
        feed = serializer.save()

        self.assertEqual(Feed.objects.count(), 1)
        self.assertEqual(feed.title, "테스트 피드")
        self.assertEqual(feed.content, "피드 내용입니다.")
        self.assertEqual(feed.image, "https://example.com/image.jpg")
        self.assertEqual(feed.tags.count(), 2)
        self.assertEqual(feed.user, self.user)
        self.assertIsNotNone(feed.uuid)

    def test_실패__제목_없음(self):
        """테스트: 제목을 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("title")

        serializer = FeedSerializer(
            data=data, context={"request": type("obj", (object,), {"user": self.user})}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)
        self.assertEqual(serializer.errors["title"][0], "이 필드는 필수 항목입니다.")

    def test_실패__내용_없음(self):
        """테스트: 내용을 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("content")

        serializer = FeedSerializer(
            data=data, context={"request": type("obj", (object,), {"user": self.user})}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("content", serializer.errors)
        self.assertEqual(serializer.errors["content"][0], "이 필드는 필수 항목입니다.")

    def test_실패__발행일_없음(self):
        """테스트: 발행일을 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("published_at")

        serializer = FeedSerializer(
            data=data, context={"request": type("obj", (object,), {"user": self.user})}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("published_at", serializer.errors)
        self.assertEqual(
            serializer.errors["published_at"][0], "이 필드는 필수 항목입니다."
        )

    def test_성공__태그_없이_피드_생성(self):
        """테스트: 태그 없이 피드 생성 성공"""
        data = self.valid_data.copy()
        data["tags"] = []

        serializer = FeedSerializer(
            data=data, context={"request": type("obj", (object,), {"user": self.user})}
        )

        self.assertTrue(serializer.is_valid())
        feed = serializer.save()

        self.assertEqual(feed.tags.count(), 0)

    def test_성공__이미지_없이_피드_생성(self):
        """테스트: 이미지 없이 피드 생성 성공"""
        data = self.valid_data.copy()
        data.pop("image")

        serializer = FeedSerializer(
            data=data, context={"request": type("obj", (object,), {"user": self.user})}
        )

        self.assertTrue(serializer.is_valid())
        feed = serializer.save()

        self.assertIsNone(feed.image)


class FeedLikeSerializerTest(TestCase):
    """피드 좋아요 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=timezone.now(),
        )

        # 유효한 좋아요 데이터
        self.valid_data = {"is_like": True}

    def test_성공__피드_좋아요_추가(self):
        """테스트: 피드 좋아요 추가 성공"""
        serializer = FeedLikeSerializer(
            instance=self.feed,
            data=self.valid_data,
            context={"request": type("obj", (object,), {"user": self.user})},
        )

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        # 좋아요 추가 확인
        self.assertTrue(result["is_like"])
        self.assertEqual(FeedLike.objects.count(), 1)

        # 피드 좋아요 수 증가 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.likes_count, 1)

    def test_성공__피드_좋아요_취소(self):
        """테스트: 피드 좋아요 취소 성공"""
        # 먼저 좋아요 추가
        FeedLike.objects.create(user=self.user, feed=self.feed)
        self.feed.likes_count = 1
        self.feed.save()

        # 좋아요 취소 데이터
        unlike_data = {"is_like": False}

        serializer = FeedLikeSerializer(
            instance=self.feed,
            data=unlike_data,
            context={"request": type("obj", (object,), {"user": self.user})},
        )

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        # 좋아요 취소 확인
        self.assertFalse(result["is_like"])
        self.assertEqual(FeedLike.objects.count(), 0)

        # 피드 좋아요 수 감소 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.likes_count, 0)

    def test_성공__이미_좋아요한_피드_재요청(self):
        """테스트: 이미 좋아요한 피드에 좋아요 재요청"""
        # 먼저 좋아요 추가
        FeedLike.objects.create(user=self.user, feed=self.feed)
        self.feed.likes_count = 1
        self.feed.save()

        serializer = FeedLikeSerializer(
            instance=self.feed,
            data=self.valid_data,
            context={"request": type("obj", (object,), {"user": self.user})},
        )

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        # 좋아요 유지 확인
        self.assertTrue(result["is_like"])
        self.assertEqual(FeedLike.objects.count(), 1)

        # 피드 좋아요 수 유지 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.likes_count, 1)


class FeedReportSerializerTest(TestCase):
    """피드 신고 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=timezone.now(),
        )

        # 다른 사용자 생성 (신고용)
        self.reporter = User.objects.create_user(
            email="reporter@example.com", password="test123"
        )

        # 유효한 신고 데이터
        self.valid_data = {
            "report_reason": FeedReportReason.INAPPROPRIATE_CONTENT,
            "content": "부적절한 내용이 포함되어 있습니다.",
        }

    def test_성공__피드_신고(self):
        """테스트: 피드 신고 성공"""
        serializer = FeedReportSerializer(
            instance=self.feed,
            data=self.valid_data,
            context={"request": type("obj", (object,), {"user": self.reporter})},
        )

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        # 신고 추가 확인
        self.assertEqual(
            result["report_reason"], FeedReportReason.INAPPROPRIATE_CONTENT
        )
        self.assertEqual(result["content"], "부적절한 내용이 포함되어 있습니다.")
        self.assertEqual(FeedReport.objects.count(), 1)

        # 피드 신고 수 증가 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.reported_count, 1)

    def test_실패__이미_신고한_피드_재신고(self):
        """테스트: 이미 신고한 피드 재신고"""
        # 먼저 신고 추가
        FeedReport.objects.create(
            user=self.reporter,
            feed=self.feed,
            report_reason=FeedReportReason.INAPPROPRIATE_CONTENT,
            content="기존 신고",
        )
        self.feed.reported_count = 1
        self.feed.save()

        serializer = FeedReportSerializer(
            instance=self.feed,
            data=self.valid_data,
            context={"request": type("obj", (object,), {"user": self.reporter})},
        )

        self.assertTrue(serializer.is_valid())

        # IntegrityError 예외 발생 확인
        with self.assertRaises(Exception) as context:
            serializer.save()

        self.assertTrue(
            E006_FEED_ALREADY_REPORTED["non_field"]["message"] in str(context.exception)
        )

    def test_성공__신고_내용_없이_피드_신고(self):
        """테스트: 신고 내용 없이 피드 신고 성공"""
        data = self.valid_data.copy()
        data.pop("content")

        serializer = FeedReportSerializer(
            instance=self.feed,
            data=data,
            context={"request": type("obj", (object,), {"user": self.reporter})},
        )

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        # 신고 추가 확인
        self.assertEqual(
            result["report_reason"], FeedReportReason.INAPPROPRIATE_CONTENT
        )
        self.assertIsNone(result.get("content"))
        self.assertEqual(FeedReport.objects.count(), 1)


class FeedCommentSerializerTest(TestCase):
    """피드 댓글 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=timezone.now(),
        )

        # 유효한 댓글 데이터
        self.valid_data = {
            "feed": str(self.feed.uuid),
            "parent": None,
            "content": "테스트 댓글입니다.",
        }

    def test_성공__댓글_생성(self):
        """테스트: 댓글 생성 성공"""
        view = FeedCommentViewSet.as_view({"get": "list"})
        view.kwargs = {"feed_pk": str(self.feed.uuid)}
        serializer = FeedCommentSerializer(
            data=self.valid_data,
            context={
                "request": type("obj", (object,), {"user": self.user}),
                "view": view,
            },
        )

        self.assertTrue(serializer.is_valid())
        comment = serializer.save()

        self.assertEqual(FeedComment.objects.count(), 1)
        self.assertEqual(comment.content, "테스트 댓글입니다.")
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.feed, self.feed)
        self.assertIsNone(comment.parent)
        self.assertIsNotNone(comment.uuid)

        # 피드 댓글 수 증가 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.comments_count, 1)

    def test_성공__대댓글_생성(self):
        """테스트: 대댓글 생성 성공"""
        # 먼저 부모 댓글 생성
        parent_comment = FeedComment.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            feed=self.feed,
            content="부모 댓글입니다.",
        )
        self.feed.comments_count = 1
        self.feed.save()

        # 대댓글 데이터
        reply_data = {
            "parent": str(parent_comment.uuid),
            "content": "대댓글입니다.",
        }

        view = FeedCommentViewSet.as_view({"get": "list"})
        view.kwargs = {"feed_pk": str(self.feed.uuid)}
        serializer = FeedCommentSerializer(
            data=reply_data,
            context={
                "request": type("obj", (object,), {"user": self.user}),
                "view": view,
            },
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))
        reply = serializer.save()

        self.assertEqual(FeedComment.objects.count(), 2)
        self.assertEqual(reply.content, "대댓글입니다.")
        self.assertEqual(reply.parent, parent_comment)

        # 부모 댓글 대댓글 수 증가 확인
        parent_comment.refresh_from_db()
        self.assertEqual(parent_comment.reply_count, 1)

        # 대댓글은 피드 댓글 수에 포함되지 않음
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.comments_count, 1)

    def test_실패__내용_없음(self):
        """테스트: 내용을 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("content")

        view = FeedCommentViewSet.as_view({"get": "list"})
        view.kwargs = {"feed_pk": str(self.feed.uuid)}
        serializer = FeedCommentSerializer(
            data=data,
            context={
                "request": type("obj", (object,), {"user": self.user}),
                "view": view,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("content", serializer.errors)
        self.assertEqual(serializer.errors["content"][0], "이 필드는 필수 항목입니다.")

    def test_실패__피드_없음(self):
        """테스트: 피드를 입력하지 않은 경우"""
        data = self.valid_data.copy()
        data.pop("feed")

        view = FeedCommentViewSet.as_view({"get": "list"})
        view.kwargs = {"feed_pk": str(uuid.uuid4())}
        serializer = FeedCommentSerializer(
            data=data,
            context={
                "request": type("obj", (object,), {"user": self.user}),
                "view": view,
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("feed", serializer.errors)
        self.assertEqual(
            serializer.errors["feed"]["message"], "피드를 찾을 수 없습니다"
        )


class FeedCommentLikeSerializerTest(TestCase):
    """피드 댓글 좋아요 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=timezone.now(),
        )

        # 테스트 댓글 생성
        self.comment = FeedComment.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            feed=self.feed,
            content="테스트 댓글입니다.",
        )

        # 유효한 좋아요 데이터
        self.valid_data = {"is_like": True}

    def test_성공__댓글_좋아요_추가(self):
        """테스트: 댓글 좋아요 추가 성공"""
        serializer = FeedCommentLikeSerializer(
            instance=self.comment,
            data=self.valid_data,
            context={"request": type("obj", (object,), {"user": self.user})},
        )

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        # 좋아요 추가 확인
        self.assertTrue(result["is_like"])
        self.assertEqual(FeedCommentLike.objects.count(), 1)

        # 댓글 좋아요 수 증가 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 1)

    def test_성공__댓글_좋아요_취소(self):
        """테스트: 댓글 좋아요 취소 성공"""
        # 먼저 좋아요 추가
        FeedCommentLike.objects.create(user=self.user, feed_comment=self.comment)
        self.comment.likes_count = 1
        self.comment.save()

        # 좋아요 취소 데이터
        unlike_data = {"is_like": False}

        serializer = FeedCommentLikeSerializer(
            instance=self.comment,
            data=unlike_data,
            context={"request": type("obj", (object,), {"user": self.user})},
        )

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        # 좋아요 취소 확인
        self.assertFalse(result["is_like"])
        self.assertEqual(FeedCommentLike.objects.count(), 0)

        # 댓글 좋아요 수 감소 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)


class FeedCommentReportSerializerTest(TestCase):
    """피드 댓글 신고 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=timezone.now(),
        )

        # 테스트 댓글 생성
        self.comment = FeedComment.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            feed=self.feed,
            content="테스트 댓글입니다.",
        )

        # 다른 사용자 생성 (신고용)
        self.reporter = User.objects.create_user(
            email="reporter@example.com", password="test123"
        )

        # 유효한 신고 데이터
        self.valid_data = {
            "report_reason": FeedReportReason.INAPPROPRIATE_CONTENT,
            "content": "부적절한 내용이 포함되어 있습니다.",
        }

    def test_성공__댓글_신고(self):
        """테스트: 댓글 신고 성공"""
        serializer = FeedCommentReportSerializer(
            instance=self.comment,
            data=self.valid_data,
            context={"request": type("obj", (object,), {"user": self.reporter})},
        )

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        # 신고 추가 확인
        self.assertEqual(
            result["report_reason"], FeedReportReason.INAPPROPRIATE_CONTENT
        )
        self.assertEqual(result["content"], "부적절한 내용이 포함되어 있습니다.")
        self.assertEqual(FeedCommentReport.objects.count(), 1)

        # 댓글 신고 수 증가 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.reported_count, 1)

    def test_실패__이미_신고한_댓글_재신고(self):
        """테스트: 이미 신고한 댓글 재신고"""
        # 먼저 신고 추가
        FeedCommentReport.objects.create(
            user=self.reporter,
            feed_comment=self.comment,
            report_reason=FeedReportReason.INAPPROPRIATE_CONTENT,
            content="기존 신고",
        )
        self.comment.reported_count = 1
        self.comment.save()

        serializer = FeedCommentReportSerializer(
            instance=self.comment,
            data=self.valid_data,
            context={"request": type("obj", (object,), {"user": self.reporter})},
        )

        self.assertTrue(serializer.is_valid())

        # IntegrityError 예외 발생 확인
        with self.assertRaises(Exception) as context:
            serializer.save()

        self.assertTrue(
            E006_COMMENT_ALREADY_REPORTED["non_field"]["message"]
            in str(context.exception)
        )


class FeedViewSetTest(APITestCase):
    """피드 뷰셋 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.feed_url = "/v1/feed/"

        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 다른 사용자 생성
        self.other_user = User.objects.create_user(
            email="other@example.com", password="test123"
        )
        self.other_profile = UserProfile.objects.create(
            user=self.other_user, nickname="otheruser"
        )

        # 현재 시간
        self.now = timezone.now()

        # 유효한 피드 데이터
        self.valid_data = {
            "title": "테스트 피드",
            "content": "피드 내용입니다.",
            "image": "https://example.com/image.jpg",
            "tags": [{"name": "태그1"}, {"name": "태그2"}],
            "published_at": self.now.isoformat(),
        }

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            title="기존 피드",
            content="기존 피드 내용입니다.",
            published_at=self.now,
        )

        # 태그 추가
        tag1 = FeedTag.objects.create(name="기존태그1")
        tag2 = FeedTag.objects.create(name="기존태그2")
        self.feed.tags.add(tag1, tag2)

        # 사용자 인증
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # 다른 사용자 인증
        other_refresh = RefreshToken.for_user(self.other_user)
        self.other_access_token = str(other_refresh.access_token)

    def test_성공__피드_생성(self):
        """테스트: 피드 생성 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(self.feed_url, data=self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feed.objects.count(), 2)  # 기존 피드 + 새 피드
        self.assertEqual(response.data["title"], "테스트 피드")
        self.assertEqual(response.data["content"], "피드 내용입니다.")
        self.assertEqual(response.data["image"], "https://example.com/image.jpg")
        self.assertEqual(len(response.data["tags"]), 2)

    def test_실패__인증_없이_피드_생성(self):
        """테스트: 인증 없이 피드 생성 시도"""
        response = self.client.post(self.feed_url, data=self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_성공__피드_리스트_조회(self):
        """테스트: 피드 리스트 조회 성공"""
        response = self.client.get(self.feed_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "기존 피드")

    def test_성공__피드_상세_조회(self):
        """테스트: 피드 상세 조회 성공"""
        response = self.client.get(f"{self.feed_url}{self.feed.uuid}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "기존 피드")
        self.assertEqual(response.data["content"], "기존 피드 내용입니다.")

    def test_성공__피드_수정(self):
        """테스트: 피드 수정 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        update_data = {
            "title": "수정된 피드",
            "content": "수정된 내용입니다.",
            "tags": [{"name": "수정태그1"}, {"name": "수정태그2"}],
            "published_at": self.now.isoformat(),
        }

        response = self.client.put(
            f"{self.feed_url}{self.feed.uuid}/", data=update_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 피드 업데이트 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.title, "수정된 피드")
        self.assertEqual(self.feed.content, "수정된 내용입니다.")

        # 태그 업데이트 확인
        tags = [tag.name for tag in self.feed.tags.all()]
        self.assertIn("수정태그1", tags)
        self.assertIn("수정태그2", tags)
        self.assertNotIn("기존태그1", tags)

    def test_실패__타인의_피드_수정(self):
        """테스트: 타인의 피드 수정 시도"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        update_data = {
            "title": "수정 시도",
            "content": "허가되지 않은 수정입니다.",
            "tags": [{"name": "태그1"}],
            "published_at": self.now.isoformat(),
        }

        response = self.client.put(
            f"{self.feed_url}{self.feed.uuid}/", data=update_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 피드 변경되지 않음 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.title, "기존 피드")

    def test_성공__피드_삭제(self):
        """테스트: 피드 삭제 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response = self.client.delete(f"{self.feed_url}{self.feed.uuid}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 피드가 표시되지 않는지 확인
        deleted_feed = Feed.objects.get(uuid=self.feed.uuid)
        self.assertTrue(deleted_feed.is_deleted)

        # 삭제된 피드는 리스트에 표시되지 않음
        response = self.client.get(self.feed_url)
        self.assertEqual(len(response.data["results"]), 0)

    def test_실패__타인의_피드_삭제(self):
        """테스트: 타인의 피드 삭제 시도"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        response = self.client.delete(f"{self.feed_url}{self.feed.uuid}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 피드 변경되지 않음 확인
        self.feed.refresh_from_db()
        self.assertFalse(self.feed.is_deleted)

    def test_성공__피드_좋아요(self):
        """테스트: 피드 좋아요 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        like_data = {"is_like": True}

        response = self.client.post(
            f"{self.feed_url}{self.feed.uuid}/like/", data=like_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_like"])

        # 피드 좋아요 수 증가 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.likes_count, 1)

        # 좋아요 객체 생성 확인
        self.assertTrue(
            FeedLike.objects.filter(user=self.user, feed=self.feed).exists()
        )

    def test_성공__피드_좋아요_취소(self):
        """테스트: 피드 좋아요 취소 성공"""
        # 먼저 좋아요 추가
        FeedLike.objects.create(user=self.user, feed=self.feed)
        self.feed.likes_count = 1
        self.feed.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        unlike_data = {"is_like": False}

        response = self.client.post(
            f"{self.feed_url}{self.feed.uuid}/like/", data=unlike_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_like"])

        # 피드 좋아요 수 감소 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.likes_count, 0)

        # 좋아요 객체 삭제 확인
        self.assertFalse(
            FeedLike.objects.filter(user=self.user, feed=self.feed).exists()
        )

    def test_성공__피드_신고(self):
        """테스트: 피드 신고 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        report_data = {
            "report_reason": FeedReportReason.INAPPROPRIATE_CONTENT,
            "content": "부적절한 내용이 포함되어 있습니다.",
        }

        response = self.client.post(
            f"{self.feed_url}{self.feed.uuid}/report/", data=report_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["report_reason"], FeedReportReason.INAPPROPRIATE_CONTENT
        )

        # 피드 신고 수 증가 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.reported_count, 1)

        # 신고 객체 생성 확인
        self.assertTrue(
            FeedReport.objects.filter(user=self.other_user, feed=self.feed).exists()
        )

    def test_실패__이미_신고한_피드_재신고(self):
        """테스트: 이미 신고한 피드 재신고"""
        # 먼저 신고 추가
        FeedReport.objects.create(
            user=self.other_user,
            feed=self.feed,
            report_reason=FeedReportReason.INAPPROPRIATE_CONTENT,
        )
        self.feed.reported_count = 1
        self.feed.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        report_data = {
            "report_reason": FeedReportReason.SPAM,
            "content": "스팸 내용입니다.",
        }

        response = self.client.post(
            f"{self.feed_url}{self.feed.uuid}/report/", data=report_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field"][0]["message"], "이미 신고된 피드입니다"
        )
        self.assertEqual(response.data["non_field"][0]["error_code"], "E0060001")

        # 피드 신고 수 변경 없음 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.reported_count, 1)

    def test_성공__태그_필터링으로_피드_조회(self):
        """테스트: 태그로 피드 필터링 조회 성공"""
        # 태그가 있는 피드 하나 더 생성
        new_feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            title="태그 테스트 피드",
            content="특정 태그가 있는 피드입니다.",
            published_at=self.now,
        )
        tag3 = FeedTag.objects.create(name="테스트태그")
        new_feed.tags.add(tag3)

        # 첫 번째 피드에도 태그 추가
        self.feed.tags.add(tag3)

        # 태그로 필터링 조회
        response = self.client.get(f"{self.feed_url}?tag=테스트태그")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # 다른 태그로 필터링
        response = self.client.get(f"{self.feed_url}?tag=기존태그1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "기존 피드")

    def test_성공__작성자로_피드_필터링(self):
        """테스트: 작성자로 피드 필터링 조회 성공"""
        # 다른 사용자의 피드 생성
        other_feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.other_user,
            title="다른 사용자의 피드",
            content="다른 사용자가 작성한 피드입니다.",
            published_at=self.now,
        )

        # 작성자로 필터링 조회
        response = self.client.get(f"{self.feed_url}?author={self.user.uuid}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "기존 피드")

        # 다른 작성자로 필터링
        response = self.client.get(f"{self.feed_url}?author={self.other_user.uuid}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "다른 사용자의 피드")


class FeedCommentViewSetTest(APITestCase):
    """피드 댓글 뷰셋 테스트"""

    def setUp(self):
        self.client = APIClient()

        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 다른 사용자 생성
        self.other_user = User.objects.create_user(
            email="other@example.com", password="test123"
        )
        self.other_profile = UserProfile.objects.create(
            user=self.other_user, nickname="otheruser"
        )

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=timezone.now(),
        )

        # API URL
        self.comment_url = f"/v1/feed/{self.feed.uuid}/comment/"

        # 테스트 댓글 생성
        self.comment = FeedComment.objects.create(
            user=self.user,
            feed=self.feed,
            content="기존 댓글입니다.",
        )
        self.feed.comments_count = 1
        self.feed.save()

        # 유효한 댓글 데이터
        self.valid_data = {
            "feed": str(self.feed.uuid),
            "parent": None,
            "content": "새 댓글입니다.",
        }

        # 사용자 인증
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # 다른 사용자 인증
        other_refresh = RefreshToken.for_user(self.other_user)
        self.other_access_token = str(other_refresh.access_token)

    def test_성공__댓글_생성(self):
        """테스트: 댓글 생성 성공"""
        with freeze_time() as freezer:
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

            # 1초 후 실행
            freezer.tick(delta=datetime.timedelta(seconds=1))

            response = self.client.post(
                self.comment_url, data=self.valid_data, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["content"], "새 댓글입니다.")

            # 피드 댓글 수 증가 확인
            self.feed.refresh_from_db()
            self.assertEqual(self.feed.comments_count, 2)

    def test_실패__인증_없이_댓글_생성(self):
        """테스트: 인증 없이 댓글 생성 시도"""
        response = self.client.post(
            self.comment_url, data=self.valid_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_성공__대댓글_생성(self):
        """테스트: 대댓글 생성 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        reply_data = {
            "feed": str(self.feed.uuid),
            "parent": str(self.comment.uuid),
            "content": "대댓글입니다.",
        }

        response = self.client.post(self.comment_url, data=reply_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "대댓글입니다.")
        self.assertEqual(str(response.data["parent"]), str(self.comment.uuid))

        # 부모 댓글의 답글 수 증가 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.reply_count, 1)

        # 대댓글은 피드 댓글 수에 포함되지 않음
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.comments_count, 1)

    def test_성공__댓글_리스트_조회(self):
        """테스트: 댓글 리스트 조회 성공"""
        response = self.client.get(self.comment_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["content"], "기존 댓글입니다.")

    def test_성공__댓글_수정(self):
        """테스트: 댓글 수정 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        update_data = {"content": "수정된 댓글입니다."}

        response = self.client.put(
            f"{self.comment_url}{self.comment.uuid}/", data=update_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 댓글 업데이트 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "수정된 댓글입니다.")

    def test_실패__타인의_댓글_수정(self):
        """테스트: 타인의 댓글 수정 시도"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        update_data = {"content": "허가되지 않은 수정입니다."}

        response = self.client.put(
            f"{self.comment_url}{self.comment.uuid}/", data=update_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 댓글 변경되지 않음 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "기존 댓글입니다.")

    def test_성공__댓글_삭제(self):
        """테스트: 댓글 삭제 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response = self.client.delete(f"{self.comment_url}{self.comment.uuid}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 피드 댓글 수 감소 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.comments_count, 0)

        # 댓글이 삭제되었는지 확인
        with self.assertRaises(FeedComment.DoesNotExist):
            FeedComment.objects.get(uuid=self.comment.uuid)

    def test_실패__타인의_댓글_삭제(self):
        """테스트: 타인의 댓글 삭제 시도"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        response = self.client.delete(f"{self.comment_url}{self.comment.uuid}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 댓글이 그대로 존재하는지 확인
        self.assertTrue(FeedComment.objects.filter(uuid=self.comment.uuid).exists())

        # 피드 댓글 수 유지 확인
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.comments_count, 1)

    def test_성공__댓글_좋아요(self):
        """테스트: 댓글 좋아요 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        like_data = {"is_like": True}

        response = self.client.post(
            f"{self.comment_url}{self.comment.uuid}/like/",
            data=like_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_like"])

        # 댓글 좋아요 수 증가 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 1)

        # 좋아요 객체 생성 확인
        self.assertTrue(
            FeedCommentLike.objects.filter(
                user=self.user, feed_comment=self.comment
            ).exists()
        )

    def test_성공__댓글_좋아요_취소(self):
        """테스트: 댓글 좋아요 취소 성공"""
        # 먼저 좋아요 추가
        FeedCommentLike.objects.create(user=self.user, feed_comment=self.comment)
        self.comment.likes_count = 1
        self.comment.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        unlike_data = {"is_like": False}

        response = self.client.post(
            f"{self.comment_url}{self.comment.uuid}/like/",
            data=unlike_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_like"])

        # 댓글 좋아요 수 감소 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)

        # 좋아요 객체 삭제 확인
        self.assertFalse(
            FeedCommentLike.objects.filter(
                user=self.user, feed_comment=self.comment
            ).exists()
        )

    def test_성공__댓글_신고(self):
        """테스트: 댓글 신고 성공"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        report_data = {
            "report_reason": FeedReportReason.INAPPROPRIATE_CONTENT,
            "content": "부적절한 내용이 포함되어 있습니다.",
        }

        response = self.client.post(
            f"{self.comment_url}{self.comment.uuid}/report/",
            data=report_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["report_reason"], FeedReportReason.INAPPROPRIATE_CONTENT
        )

        # 댓글 신고 수 증가 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.reported_count, 1)

        # 신고 객체 생성 확인
        self.assertTrue(
            FeedCommentReport.objects.filter(
                user=self.other_user, feed_comment=self.comment
            ).exists()
        )

    def test_실패__이미_신고한_댓글_재신고(self):
        """테스트: 이미 신고한 댓글 재신고"""
        # 먼저 신고 추가
        FeedCommentReport.objects.create(
            user=self.other_user,
            feed_comment=self.comment,
            report_reason=FeedReportReason.INAPPROPRIATE_CONTENT,
        )
        self.comment.reported_count = 1
        self.comment.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        report_data = {
            "report_reason": FeedReportReason.SPAM,
            "content": "스팸 내용입니다.",
        }

        response = self.client.post(
            f"{self.comment_url}{self.comment.uuid}/report/",
            data=report_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field"][0]["message"], "이미 신고된 피드 댓글입니다"
        )
        self.assertEqual(response.data["non_field"][0]["error_code"], "E0060002")

        # 댓글 신고 수 변경 없음 확인
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.reported_count, 1)

    def test_성공__부모_댓글_필터링으로_대댓글_조회(self):
        """테스트: 부모 댓글로 필터링하여 대댓글 조회 성공"""
        # 대댓글 생성
        reply1 = FeedComment.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            feed=self.feed,
            parent=self.comment,
            content="첫 번째 대댓글입니다.",
        )

        reply2 = FeedComment.objects.create(
            uuid=uuid.uuid4(),
            user=self.other_user,
            feed=self.feed,
            parent=self.comment,
            content="두 번째 대댓글입니다.",
        )

        # 부모 댓글의 답글 수 업데이트
        self.comment.reply_count = 2
        self.comment.save()

        # 부모 댓글로 필터링하여 대댓글 조회
        response = self.client.get(f"{self.comment_url}?parent={self.comment.uuid}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # 결과에 두 대댓글이 모두 포함되었는지 확인
        contents = [comment["content"] for comment in response.data["results"]]
        self.assertIn("첫 번째 대댓글입니다.", contents)
        self.assertIn("두 번째 대댓글입니다.", contents)


class XSSPreventionTest(TestCase):
    """XSS 방지 기능 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 현재 시간
        self.now = timezone.now()

    def test_댓글_XSS_방지(self):
        """테스트: 댓글 생성 시 XSS 방지"""
        # 테스트 피드 생성
        feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=self.now,
        )

        xss_data = {
            "feed": str(feed.uuid),
            "content": "<script>alert('XSS 공격');</script>",
        }

        view = FeedCommentViewSet.as_view({"get": "list"})
        view.kwargs = {"feed_pk": str(feed.uuid)}
        serializer = FeedCommentSerializer(
            data=xss_data,
            context={
                "request": type("obj", (object,), {"user": self.user}),
                "view": view,
            },
        )

        self.assertTrue(serializer.is_valid())
        comment = serializer.save()

        # XSS 코드가 이스케이프 되어 저장되었는지 확인
        self.assertEqual(
            comment.content, "&lt;script&gt;alert('XSS 공격');&lt;/script&gt;"
        )


class FeedListRetrieveSerializerTest(TestCase):
    """피드 리스트/상세 시리얼라이저 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 현재 시간
        self.now = timezone.now()

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=self.now,
        )

        # 태그 추가
        tag = FeedTag.objects.create(name="테스트태그")
        self.feed.tags.add(tag)

    def test_성공__FeedListSerializer(self):
        """테스트: FeedListSerializer 정상 동작"""
        serializer = FeedListSerializer(instance=self.feed)
        data = serializer.data

        self.assertEqual(data["uuid"], str(self.feed.uuid))
        self.assertEqual(data["title"], "테스트 피드")
        self.assertEqual(data["author"]["nickname"], "testuser")
        self.assertFalse(data["is_like"])
        self.assertFalse(data["is_reported"])
        self.assertIsNone(data["best_comment"])

    def test_성공__FeedRetrieveSerializer(self):
        """테스트: FeedRetrieveSerializer 정상 동작"""
        serializer = FeedRetrieveSerializer(instance=self.feed)
        data = serializer.data

        self.assertEqual(data["uuid"], str(self.feed.uuid))
        self.assertEqual(data["title"], "테스트 피드")
        self.assertEqual(data["author"]["nickname"], "testuser")
        self.assertEqual(len(data["tags"]), 1)
        self.assertEqual(data["tags"][0]["name"], "테스트태그")

    def test_성공__베스트_댓글_포함(self):
        """테스트: 베스트 댓글이 포함된 경우"""
        # 좋아요가 1개 이상인 댓글 생성
        comment = FeedComment.objects.create(
            uuid=uuid.uuid4(),
            user=self.user,
            feed=self.feed,
            content="베스트 댓글입니다.",
            likes_count=5,
        )

        serializer = FeedListSerializer(instance=self.feed)
        data = serializer.data

        self.assertIsNotNone(data["best_comment"])
        self.assertEqual(data["best_comment"]["content"], "베스트 댓글입니다.")
        self.assertEqual(data["best_comment"]["likes_count"], 5)


class CurrentFeedDefaultTest(TestCase):
    """CurrentFeedDefault 필드 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=timezone.now(),
        )

    def test_성공__CurrentFeedDefault_동작(self):
        """테스트: CurrentFeedDefault 필드 동작 확인"""
        field = CurrentFeedDefault()

        # 가상의 컨텍스트 생성
        view = type("obj", (object,), {})
        view.kwargs = {"feed_pk": str(self.feed.uuid)}

        serializer_field = type("obj", (object,), {"context": {"view": view}})

        # 필드 호출 결과 확인
        result = field(serializer_field)
        self.assertEqual(result, str(self.feed.uuid))


class PaginationTest(APITestCase):
    """페이지네이션 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.feed_url = "/v1/feed/"

        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 사용자 인증
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # 여러 개의 피드 생성 (총 15개)
        current_time = timezone.now()
        for i in range(15):
            Feed.objects.create(
                user=self.user,
                title=f"테스트 피드 {i + 1}",
                content=f"피드 내용 {i + 1}입니다.",
                published_at=current_time - timedelta(hours=i),  # 시간차를 둠
            )

    def test_성공__피드_페이지네이션(self):
        """테스트: 피드 페이지네이션 동작 확인"""
        # 첫 페이지 요청
        response = self.client.get(self.feed_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)  # 기본 페이지 크기는 10
        self.assertIsNotNone(response.data.get("next"))  # 다음 페이지 존재
        self.assertIsNone(response.data.get("previous"))  # 이전 페이지 없음

        # 다음 페이지 요청
        next_url = response.data["next"]
        next_path = next_url.split("http://testserver")[1]  # URL에서 path 부분만 추출

        response2 = self.client.get(next_path)

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data["results"]), 5)  # 남은 5개 항목
        self.assertIsNone(response2.data.get("next"))  # 다음 페이지 없음
        self.assertIsNotNone(response2.data.get("previous"))  # 이전 페이지 존재


class FeedFilteringTest(APITestCase):
    """피드 필터링 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.feed_url = "/v1/feed/"

        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 현재 시간
        now = timezone.now()

        # 다양한 피드 생성
        # 1. 일반 피드
        self.feed1 = Feed.objects.create(
            user=self.user,
            title="일반 피드",
            content="일반 내용입니다.",
            published_at=now - timedelta(days=1),
        )

        # 2. 프로그래밍 관련 피드
        self.feed2 = Feed.objects.create(
            user=self.user,
            title="프로그래밍 팁",
            content="파이썬 프로그래밍 팁입니다.",
            published_at=now - timedelta(days=2),
        )

        # 3. 오래된 피드
        self.feed3 = Feed.objects.create(
            user=self.user,
            title="오래된 피드",
            content="오래된 내용입니다.",
            published_at=now - timedelta(days=10),
        )

        # 태그 추가
        tag1 = FeedTag.objects.create(name="일반")
        tag2 = FeedTag.objects.create(name="프로그래밍")

        self.feed1.tags.add(tag1)
        self.feed2.tags.add(tag2)
        self.feed3.tags.add(tag1, tag2)  # 두 태그 모두 추가

    def test_성공__제목_필터링(self):
        """테스트: 제목으로 피드 필터링"""
        # '프로그래밍'이 제목에 포함된 피드 검색
        response = self.client.get(f"{self.feed_url}?title__icontains=프로그래밍")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "프로그래밍 팁")


class ThrottlingTest(APITestCase):
    """요청 속도 제한(쓰로틀링) 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.feed_url = "/v1/feed/"

        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 현재 시간
        self.now = timezone.now()

        # 유효한 피드 데이터
        self.valid_data = {
            "title": "테스트 피드",
            "content": "피드 내용입니다.",
            "tags": [{"name": "태그1"}],
            "published_at": self.now.isoformat(),
        }

        # 사용자 인증
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # 캐시 초기화
        cache.clear()

    @patch("rest_framework.throttling.ScopedRateThrottle.get_rate")
    def test_실패__피드_생성_속도_제한(self, mock_get_rate):
        """테스트: 피드 생성 속도 제한"""
        # 테스트를 위해 더 엄격한 속도 제한 적용 (1/hour)
        mock_get_rate.return_value = "1/hour"

        # 인증 설정
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # 첫 번째 요청 (성공해야 함)
        response1 = self.client.post(self.feed_url, data=self.valid_data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # 두 번째 요청 (속도 제한에 걸려야 함)
        response2 = self.client.post(self.feed_url, data=self.valid_data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class ErrorHandlingTest(APITestCase):
    """에러 핸들링 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.feed_url = "/v1/feed/"
        self.invalid_uuid = "not-a-valid-uuid"

        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 사용자 인증
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_실패__잘못된_UUID_형식(self):
        """테스트: 잘못된 UUID 형식으로 피드 조회"""
        # 인증 설정
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # 잘못된 UUID로 피드 조회
        response = self.client.get(f"{self.feed_url}{self.invalid_uuid}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_실패__존재하지_않는_피드_UUID(self):
        """테스트: 존재하지 않는 UUID로 피드 조회"""
        # 존재하지 않는 유효한 UUID 형식
        non_existent_uuid = uuid.uuid4()

        # 피드 조회
        response = self.client.get(f"{self.feed_url}{non_existent_uuid}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FeedModelMethodTest(TestCase):
    """피드 모델 메서드 테스트"""

    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=timezone.now(),
        )

        # 태그 추가
        tag1 = FeedTag.objects.create(name="테스트태그1")
        tag2 = FeedTag.objects.create(name="테스트태그2")
        self.feed.tags.add(tag1, tag2)


class FeedCommentFilterTest(APITestCase):
    """피드 댓글 필터링 테스트"""

    def setUp(self):
        self.client = APIClient()

        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.profile = UserProfile.objects.create(user=self.user, nickname="testuser")

        # 테스트 피드 생성
        self.feed = Feed.objects.create(
            user=self.user,
            title="테스트 피드",
            content="피드 내용입니다.",
            published_at=timezone.now(),
        )

        # API URL
        self.comment_url = f"/v1/feed/{self.feed.uuid}/comment/"

        # 부모 댓글 생성
        self.parent_comment1 = FeedComment.objects.create(
            user=self.user,
            feed=self.feed,
            content="첫 번째 부모 댓글입니다.",
        )

        self.parent_comment2 = FeedComment.objects.create(
            user=self.user,
            feed=self.feed,
            content="두 번째 부모 댓글입니다.",
        )

        # 대댓글 생성
        self.reply1 = FeedComment.objects.create(
            user=self.user,
            feed=self.feed,
            parent=self.parent_comment1,
            content="첫 번째 부모 댓글의 대댓글 1입니다.",
        )

        self.reply2 = FeedComment.objects.create(
            user=self.user,
            feed=self.feed,
            parent=self.parent_comment1,
            content="첫 번째 부모 댓글의 대댓글 2입니다.",
        )

        self.reply3 = FeedComment.objects.create(
            user=self.user,
            feed=self.feed,
            parent=self.parent_comment2,
            content="두 번째 부모 댓글의 대댓글입니다.",
        )

        # 부모 댓글의 대댓글 수 업데이트
        self.parent_comment1.reply_count = 2
        self.parent_comment1.save()

        self.parent_comment2.reply_count = 1
        self.parent_comment2.save()

        # 피드의 댓글 수 업데이트
        self.feed.comments_count = 2
        self.feed.save()

    def test_성공__특정_부모_댓글의_대댓글만_조회(self):
        """테스트: 특정 부모 댓글의 대댓글만 조회"""
        # parent가 parent_comment1인 댓글만 조회
        response = self.client.get(
            f"{self.comment_url}?parent={self.parent_comment1.uuid}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # 대댓글 2개만 나와야 함

        # 대댓글 ID 목록 확인
        reply_ids = [reply["uuid"] for reply in response.data["results"]]
        self.assertIn(str(self.reply1.uuid), reply_ids)
        self.assertIn(str(self.reply2.uuid), reply_ids)
        self.assertNotIn(str(self.reply3.uuid), reply_ids)
