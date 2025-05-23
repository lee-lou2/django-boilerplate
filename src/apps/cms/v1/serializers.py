from django.utils import timezone
from rest_framework import serializers

from apps.cms.models import Notice, Event, Faq, FaqCategory


class NoticeSerializer(serializers.ModelSerializer):
    """
    Notice Serializer:
    List and detail view for notices.
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
    Event Serializer:
    List and detail view for events.
    Indicates whether the event has ended.
    """

    is_event_ended = serializers.SerializerMethodField(
        method_name="get_is_event_ended",
        help_text="Indicates if the event has ended",
    )

    def get_is_event_ended(self, obj):
        """Check if the event has ended"""
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
    FAQ Category Serializer:
    Category information for FAQ list and detail views.
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
    FAQ Serializer:
    List and detail view for FAQs.
    """

    category = FaqCategorySerializer(help_text="FAQ Category")

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
