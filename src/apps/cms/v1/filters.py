from django_filters import rest_framework as filters

from apps.cms.models import Notice, Event, Faq


class NoticeFilterSet(filters.FilterSet):
    """공지사항 필터셋"""

    class Meta:
        model = Notice
        fields = {
            "title": ["exact", "icontains"],
            "published_at": ["gte", "lte"],
        }


class EventFilterSet(filters.FilterSet):
    """이벤트 필터셋"""

    class Meta:
        model = Event
        fields = {
            "title": ["exact", "icontains"],
            "published_at": ["gte", "lte"],
        }


class FaqFilterSet(filters.FilterSet):
    """FAQ 필터셋"""

    category_name = filters.CharFilter(
        field_name="category__name",
        lookup_expr="icontains",
        label="카테고리 이름",
    )

    class Meta:
        model = Faq
        fields = {
            "published_at": ["gte", "lte"],
        }
