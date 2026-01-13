from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import ScopedRateThrottle

from apps.feed.models import (
    Feed,
    FeedLike,
    FeedReport,
    FeedComment,
    FeedCommentLike,
    FeedCommentReport,
)
from apps.feed.v1.filters import FeedFilterSet, FeedCommentFilterSet
from apps.feed.v1.paginations import FeedCursorPagination, FeedCommentCursorPagination
from apps.feed.v1.serializers import (
    FeedSerializer,
    FeedReportSerializer,
    FeedLikeSerializer,
    FeedCommentSerializer,
    FeedListSerializer,
    FeedRetrieveSerializer,
    FeedCommentListSerializer,
    FeedCommentReportSerializer,
    FeedCommentLikeSerializer,
)


class FeedViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    """피드 뷰셋"""

    queryset = Feed.objects.filter(is_deleted=False)
    serializer_class = FeedSerializer  # get_serializer_class 에서 변경
    permission_classes = [AllowAny]  # get_permissions 에서 변경
    filterset_class = FeedFilterSet
    pagination_class = FeedCursorPagination
    throttle_scope = "feed"

    def get_permissions(self):
        """권한 조회"""
        # 리스트, 상세 조회 외에는 인증 필요
        if self.action not in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_throttles(self):
        """요청 속도 제한 설정"""
        # 생성, 좋아요, 신고 시 속도 제한
        if self.action in ["create", "like", "report"]:
            self.throttle_scope = f"{self.throttle_scope}:{self.action}"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_serializer_class(self):
        """시리얼라이저 조회"""
        if self.action == "list":
            return FeedListSerializer
        elif self.action == "retrieve":
            return FeedRetrieveSerializer
        elif self.action == "like":
            return FeedLikeSerializer
        elif self.action == "report":
            return FeedReportSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """쿼리셋 조회"""
        queryset = super().get_queryset()
        if self.action in ["update", "destroy"]:
            queryset = queryset.filter(user=self.request.user)
        if self.action not in ["list", "retrieve"]:
            return queryset
        # 리스트, 상세 조회 시
        queryset = (
            queryset.select_related("user__profile")
            .prefetch_related("feed_comments")
            .filter(published_at__lte=timezone.now())
        )
        # 인증된 사용자일 경우 좋아요/신고 여부 조회
        if self.request.user.is_authenticated:
            # 로그인 사용자의 좋아요/신고 여부
            queryset = queryset.prefetch_related("feed_likes", "feed_reports").annotate(
                is_like=Exists(
                    FeedLike.objects.filter(feed=OuterRef("pk"), user=self.request.user)
                ),
                is_reported=Exists(
                    FeedReport.objects.filter(
                        feed=OuterRef("pk"), user=self.request.user
                    )
                ),
            )
        return queryset

    @extend_schema(
        request=FeedSerializer,
        responses={
            201: FeedSerializer,
        },
        tags=["feed"],
        summary="피드 생성",
        description="""
        피드를 생성합니다.
        태그는 여러 개를 선택할 수 있습니다.
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        responses={
            200: FeedSerializer(many=True),
        },
        tags=["feed"],
        summary="피드 리스트 조회",
        description="""
        피드 리스트를 조회합니다.
        """,
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={
            200: FeedSerializer,
        },
        tags=["feed"],
        summary="피드 상세 조회",
        description="""
        피드를 상세 조회합니다.
        """,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @extend_schema(
        responses={
            204: None,
        },
        tags=["feed"],
        summary="피드 삭제",
        description="""
        피드를 삭제합니다.
        """,
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        request=FeedSerializer,
        responses={
            200: FeedSerializer,
        },
        tags=["feed"],
        summary="피드 수정",
        description="""
        피드를 수정합니다.
        """,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def partial_update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PATCH method not allowed")

    @extend_schema(
        request=FeedLikeSerializer,
        responses={
            200: FeedLikeSerializer,
        },
        tags=["feed"],
        summary="피드 좋아요",
        description="""
        피드를 좋아요합니다.
        """,
    )
    @action(detail=True, methods=["POST"], serializer_class=FeedLikeSerializer)
    def like(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=FeedReportSerializer,
        responses={
            200: FeedReportSerializer,
        },
        tags=["feed"],
        summary="피드 신고",
        description="""
        피드를 신고합니다.
        """,
    )
    @action(detail=True, methods=["POST"], serializer_class=FeedReportSerializer)
    def report(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class FeedCommentViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    """피드 댓글 뷰셋"""

    queryset = FeedComment.objects.filter(is_displayed=True)
    serializer_class = FeedCommentSerializer  # get_serializer_class 에서 변경
    permission_classes = [AllowAny]  # get_permissions 에서 변경
    filterset_class = FeedCommentFilterSet
    pagination_class = FeedCommentCursorPagination
    throttle_scope = "comment"

    def get_permissions(self):
        """권한 조회"""
        # 리스트, 상세 조회 외에는 인증 필요
        if self.action != "list":
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_throttles(self):
        """요청 속도 제한 설정"""
        # 생성, 좋아요, 신고 시 속도 제한
        if self.action in ["create", "like", "report"]:
            self.throttle_scope = f"{self.throttle_scope}:{self.action}"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        """쿼리셋 조회"""
        queryset = super().get_queryset()
        # 해당 피드 조회
        feed_uuid = self.kwargs.get("feed_pk")
        queryset = queryset.filter(feed__uuid=feed_uuid)
        # 피드 업데이트, 삭제는 작성자만 가능
        if self.action in ["update", "destroy"]:
            queryset = queryset.filter(user=self.request.user)
        if self.action != "list":
            return queryset
        # 리스트 조회 시
        queryset = queryset.select_related("user__profile").prefetch_related("replies")
        if self.request.user.is_authenticated:
            # 로그인 사용자의 경우 좋아요 여부
            queryset = queryset.prefetch_related(
                "feed_comment_likes", "feed_comment_reports"
            ).annotate(
                is_like=Exists(
                    FeedCommentLike.objects.filter(
                        feed_comment=OuterRef("pk"), user=self.request.user
                    )
                ),
                is_reported=Exists(
                    FeedCommentReport.objects.filter(
                        feed_comment=OuterRef("pk"), user=self.request.user
                    )
                ),
            )
        return queryset

    def get_serializer_class(self):
        """시리얼라이저 조회"""
        if self.action == "list":
            return FeedCommentListSerializer
        elif self.action == "like":
            return FeedCommentLikeSerializer
        elif self.action == "report":
            return FeedCommentReportSerializer
        return FeedCommentSerializer

    @extend_schema(
        request=FeedCommentSerializer,
        responses={
            201: FeedCommentSerializer,
        },
        tags=["feed"],
        summary="피드 댓글 생성",
        description="""
        피드를 댓글을 생성합니다.
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        responses={
            200: FeedCommentListSerializer(many=True),
        },
        tags=["feed"],
        summary="피드 댓글 리스트 조회",
        description="""
        피드 댓글 리스트를 조회합니다.
        일반 댓글과 대댓글을 구분하여 조회합니다.
        """,
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        request=FeedCommentSerializer,
        responses={
            200: FeedCommentSerializer,
        },
        tags=["feed"],
        summary="피드 댓글 수정",
        description="""
        피드 댓글을 수정합니다.
        """,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def partial_update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PATCH method not allowed")

    @transaction.atomic
    def perform_destroy(self, instance):
        # 피드의 댓글 수 감소
        if instance.parent is None:
            instance.feed.comments_count -= 1 if instance.feed.comments_count > 0 else 0
            instance.feed.save()
        # 부모 댓글의 답글 수 감소
        if instance.parent:
            instance.parent.reply_count -= 1 if instance.parent.reply_count > 0 else 0
            instance.parent.save()
        return super().perform_destroy(instance)

    @extend_schema(
        responses={
            204: None,
        },
        tags=["feed"],
        summary="피드 댓글 삭제",
        description="""
        피드 댓글을 삭제합니다.
        """,
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        request=FeedCommentLikeSerializer,
        responses={
            200: FeedCommentLikeSerializer,
        },
        tags=["feed"],
        summary="피드 댓글 좋아요",
        description="""
        피드 댓글을 좋아요합니다.
        """,
    )
    @action(detail=True, methods=["POST"], serializer_class=FeedCommentLikeSerializer)
    def like(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=FeedCommentReportSerializer,
        responses={
            200: FeedCommentReportSerializer,
        },
        tags=["feed"],
        summary="피드 댓글 신고",
        description="""
        피드 댓글을 신고합니다.
        """,
    )
    @action(detail=True, methods=["POST"], serializer_class=FeedCommentReportSerializer)
    def report(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
