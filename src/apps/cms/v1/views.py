from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from apps.cms.models import Notice, Event, Faq
from apps.cms.v1.filters import NoticeFilterSet, EventFilterSet, FaqFilterSet
from apps.cms.v1.serializers import NoticeSerializer, EventSerializer, FaqSerializer


class NoticeViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
):
    """공지사항 뷰셋"""

    queryset = Notice.objects.filter(is_published=True)
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = NoticeFilterSet

    def get_queryset(self):
        now = timezone.now()
        return self.queryset.filter(
            Q(end_at__gte=now) | Q(end_at__isnull=True),
            start_at__lte=now,
        )

    @extend_schema(
        responses={
            200: NoticeSerializer(many=True),
        },
        tags=["cms"],
        summary="공지사항 리스트 조회",
        description="""
        공지사항 리스트를 조회합니다.
        """,
    )
    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={
            200: NoticeSerializer,
        },
        tags=["cms"],
        summary="공지사항 상세 조회",
        description="""
        공지사항 상세를 조회합니다.
        """,
    )
    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class EventViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
):
    """이벤트 뷰셋"""

    queryset = Event.objects.filter(is_published=True)
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = EventFilterSet

    def get_queryset(self):
        now = timezone.now()
        return self.queryset.filter(
            Q(end_at__gte=now) | Q(end_at__isnull=True),
            start_at__lte=now,
        )

    @extend_schema(
        responses={
            200: EventSerializer(many=True),
        },
        tags=["cms"],
        summary="이벤트 리스트 조회",
        description="""
        이벤트 리스트를 조회합니다.
        """,
    )
    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={
            200: EventSerializer,
        },
        tags=["cms"],
        summary="이벤트 상세 조회",
        description="""
        이벤트 상세를 조회합니다.
        """,
    )
    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class FaqViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
):
    """FAQ 뷰셋"""

    queryset = Faq.objects.filter(is_published=True)
    serializer_class = FaqSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = FaqFilterSet

    @extend_schema(
        responses={
            200: FaqSerializer(many=True),
        },
        tags=["cms"],
        summary="FAQ 리스트 조회",
        description="""
        FAQ 리스트를 조회합니다.
        """,
    )
    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
