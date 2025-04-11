from django.utils import timezone
from rest_framework import serializers

from apps.cms.models import Notice, Event, Faq, FaqCategory


class NoticeSerializer(serializers.ModelSerializer):
    """
    공지사항 시리얼라이저:
    공지사항 리스트 및 상세 조회
    """

    class Meta:
        model = Notice
        fields = [
            "uuid",
            "title",
            "content",
            "published_at",
            "start_at",
            "end_at",
            "created_at",
            "updated_at",
        ]


class EventSerializer(serializers.ModelSerializer):
    """
    이벤트 시리얼라이저:
    이벤트 리스트 및 상세 조회
    종료된 이벤트 여부 표시
    """

    is_event_ended = serializers.SerializerMethodField(
        method_name="get_is_event_ended",
        help_text="이벤트 종료 여부",
    )

    def get_is_event_ended(self, obj):
        """이벤트 종료 여부 확인"""
        return obj.event_end_at <= timezone.now() if obj.event_end_at else False

    class Meta:
        model = Event
        fields = [
            "uuid",
            "title",
            "content",
            "published_at",
            "start_at",
            "end_at",
            "event_start_at",
            "event_end_at",
            "is_event_ended",
            "created_at",
            "updated_at",
        ]


class FaqCategorySerializer(serializers.ModelSerializer):
    """
    FAQ 카테고리 시리얼라이저:
    FAQ 리스트 및 상세 조회 시 카테고리 정보
    """

    class Meta:
        model = FaqCategory
        fields = [
            "uuid",
            "name",
            "created_at",
            "updated_at",
        ]


class FaqSerializer(serializers.ModelSerializer):
    """
    FAQ 시리얼라이저:
    FAQ 리스트 및 상세 조회
    """

    category = FaqCategorySerializer(help_text="FAQ 카테고리")

    class Meta:
        model = Faq
        fields = [
            "uuid",
            "category",
            "title",
            "content",
            "published_at",
            "created_at",
            "updated_at",
        ]
